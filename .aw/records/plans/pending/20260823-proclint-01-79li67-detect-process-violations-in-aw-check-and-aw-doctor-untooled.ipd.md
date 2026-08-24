# IPD: Detect process violations in aw check and aw doctor (untooled status changes, unattributed transitions)

- Date: 2026-08-23
- Kind: child
- Concern: Process steps this toolkit requires (change lifecycle status via `aw set`, not by hand-editing the `- Status:` line) are enforced only by soft prose in AGENTS.md and are consistently dropped by ALL current agents (cross-vendor, observed repeatedly - including a reviewer that hand-edited `- Status: reviewed -> to-review` on five plans in this very repo instead of using `aw set`). There is today NO deterministic DETECTION of a status that changed without a corresponding tool-authored `## Workflow history` transition entry, so a hand-edited status is invisible to `aw check`/`aw doctor`. This is the DETECTIVE half of the reliability problem (the preventive half - hard gates, delegation, hooks - is the subject of research prompt `9bd3j8` and the `ipdgates` Set); this IPD adds the low-false-positive post-hoc detector.
- Scope: Add a deterministic checker that flags an artifact whose current `- Status:` has no matching tool-authored `## Workflow history` transition line (the signature of a hand-edited status), surfaced through `aw check` and `aw doctor` with an actionable, self-documenting remediation. Touch: agent_workflows/check_engine.py (new rule), agent_workflows/doctor.py (remediation mapping), and tests. Explicitly does NOT re-implement the id6-identity-slot check (unifyfileio Order 05 `9a655p`) nor the terminal-history generic-actor lint (ipdgates Order 07 `wezhxg`); it cross-references them and covers the DISTINCT "status changed without a tool-authored transition record" violation.
- Status: draft
- Set: proclint
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 79li67

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created at maintainer direction, as the DETECTIVE counterpart to research prompt `9bd3j8` (preventive/how-to-make-adherence-stick) - "aw check/aw doctor should flag things done improperly if possible."

## Goal

Give `aw check` and `aw doctor` a deterministic, low-false-positive way to catch the most common untooled process violation: a `- Status:` value that was changed by hand (or by any non-`aw` path) and therefore lacks a corresponding tool-authored `## Workflow history` transition entry. `aw set`/`aw ipd set` always append a `- <date> <status> (<actor>): <message>` line when they transition status (`status_set.py:463`); a status whose current value has no such matching terminal-history line is the fingerprint of a bypass. Flag it with an actionable remediation ("status appears hand-edited; transition via `aw set <status> <id>` so the change is attributed"), WITHOUT firing on legitimate historical records (grandfather pre-existing artifacts, mirroring the ipdgates forward-only convention) or on artifact types that do not carry a `## Workflow history` section.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The status-vs-history consistency detector

- [ ] E-01 In `agent_workflows/check_engine.py`, add a rule (e.g. `check.status-untooled`) that, for each artifact type carrying a `## Workflow history`, parses the current `- Status:` and the history lines, and flags when the current status has NO matching tool-authored transition entry for that status value (the signature of a hand-edited status). Reuse the existing history-line parsing where possible (extend `ipd_lint`'s `_HISTORY_LINE_RE` / `doc.history_lines` rather than a second parser). Fire fail-closed with the standard `Drift`/exit convention. Grandfather: apply only to status values set AFTER a defined cutoff (mirror the ipdgates/`Scope-Paths` forward-only cutoff, or a simpler "has ANY tool-authored history line at all" heuristic for pre-existing records) so the existing tree is not mass-flagged.
  - Depends on: none
  - Expected outcome: `aw check` flags an artifact whose current `- Status:` has no matching tool-authored history transition, and stays clean on a properly-transitioned tree.
  - Execution state: pending

### Task group 2: Doctor remediation

- [ ] E-02 Map the new rule into `agent_workflows/doctor.py` so `aw doctor` reports it with a self-documenting remediation that names the exact fix ("this status looks hand-edited; re-apply it via `aw set <status> <id6>` so it carries an attributed history entry"), consistent with how doctor renders other `check_engine` drift. The message TEACHES the correct tool path (self-documenting principle), it does not merely fail.
  - Depends on: E-01
  - Expected outcome: `aw doctor --agent` lists the untooled-status violation with an actionable, tool-naming remediation.
  - Execution state: pending

### Task group 3: Prove detection + no false positives + grandfather

- [ ] E-03 Add tests: a fixture whose `- Status:` was hand-edited (changed with no matching tool-authored history line) is FLAGGED; a fixture transitioned via `aw set` (status + matching attributed history line) is CLEAN; a pre-cutoff/grandfathered record with no tooled history is NOT flagged (no mass retroactive failure); an artifact type with no `## Workflow history` section is not falsely flagged. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: the hand-edit is caught, the tooled path is clean, and neither the grandfathered tree nor history-less types produce false positives.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw set`/`aw ipd set` append `- <date> <status> (<actor>): <message>` to `## Workflow history` on every transition (`status_set.py:463`); the generic default actor is `aw set` (`status_set.py:356`). A hand-edited `- Status:` produces NO such line - that asymmetry is the detection signal.
- `check_engine.py` composes per-type `Drift` rules consumed by `aw check`; `doctor.py` maps rules to remediations. This IPD adds one rule + one remediation, mirroring the existing pattern.
- Cross-references (do NOT duplicate): the terminal-history generic-actor/empty-summary lint is ipdgates Order 07 (`wezhxg`); the id6-identity-slot check is unifyfileio Order 05 (`9a655p`). This IPD covers the DISTINCT "status changed with no tool-authored transition at all" violation.
- Forward-only grandfathering is the established convention (ipdgates) to avoid mass retroactive failure of immutable/pre-existing records.

## Findings

Soft prose enforcement of "use `aw set`" is not working across any agent; a deterministic post-hoc detector converts the invisible bypass into a visible, actionable finding. The design constraint is FALSE POSITIVES: the check must not fire on legitimate pre-existing records (grandfather) or on artifacts that never carry a `## Workflow history`, or agents/humans will learn to ignore it (which would defeat its purpose). Detection is a safety net, not prevention; the preventive layer (hard gates / delegation / hooks) is research prompt `9bd3j8` + the `ipdgates` Set.

## Proposed changes (ordered, validatable)

1. Add the `check.status-untooled` rule to `check_engine.py` (status-vs-history consistency, grandfathered) (E-01).
2. Map it to a self-documenting `aw doctor` remediation (E-02).
3. Tests: hand-edit flagged, tooled clean, grandfathered clean, history-less types clean (E-03).

## Deferred / out of scope (with reason)

- The PREVENTIVE layer (hard gates, `aw set` delegation, host hooks, making the wrong action impossible): research prompt `9bd3j8` + the `ipdgates` Set; this IPD is detection only.
- Terminal-history generic-actor lint and id6-identity-slot check: owned by ipdgates Order 07 and unifyfileio Order 05 respectively; cross-referenced, not duplicated.
- Detecting non-status process violations (out-of-scope commits, missing IPD before coding, unpushed/pushed policy): candidate FUTURE proclint children informed by `9bd3j8`; not this IPD.
- A git pre-commit hook variant of the detector: possible follow-up; this IPD delivers the `aw check`/`aw doctor` surface.

## Scope check

- Over-scope: none. One detection rule + its remediation + tests.
- Under-scope: none for the untooled-status violation; other process violations are deliberately deferred to future proclint children pending `9bd3j8`.

## Required tests / validation

- Tests per E-03 (hand-edited flagged; tooled clean; grandfathered clean; history-less type clean).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Document the new `check.status-untooled` rule in the check-rule list / `aw check`/`aw doctor` help (via managed verbs); note it is a DETECTOR (the preventive path is `aw set`). Else N/A with reason.

## Open questions

### OQ-01: What exactly distinguishes a "tool-authored" history line from a hand-written one, and how is the grandfather cutoff defined?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). Two coupled sub-questions: (1) DETECTION PREDICATE - a hand-editor can also hand-write a plausible `- <date> <status> (someactor): ...` line, so a purely textual "is there a matching line" check can be spoofed. Options: (A) accept the textual heuristic (catches the common careless hand-edit where NO line was added - which is the actual observed failure - while acknowledging a determined forger can evade it; detection surfaces + attributes, it does not prove); (B) require a stronger tool-authored marker that `aw set` writes and a hand-edit is unlikely to reproduce (e.g. a structured signature), at the cost of changing `aw set`'s output format and a migration. (2) GRANDFATHER CUTOFF - reuse the ipdgates/`Scope-Paths` cutoff mechanism (a dated/marker predicate) or the simpler "grandfather any record with no tooled history line at all" heuristic. The executor MUST get a human decision on the predicate strength (A vs B) and the cutoff before E-01, since it defines both what is caught and what is grandfathered. (A is likely sufficient given the observed failure is careless omission, not forgery.)

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a unit test drives `check_engine` on a fixture whose `- Status:` was changed with NO matching tool-authored history line and asserts a `check.status-untooled` Drift; a fixture transitioned via `aw set` (status + attributed line) yields none; a grandfathered pre-cutoff record and a history-less artifact type each yield none.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a test asserts `aw doctor` (human and `--agent`) renders the new rule with a remediation that names `aw set <status> <id>` as the fix.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the full detection test set (hand-edit flagged, tooled clean, grandfathered clean, history-less clean) passes and `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - a deterministic post-hoc detector for untooled status changes, surfaced via `aw check`/`aw doctor`.

### Execution contract

1. Open questions RESOLVED: OQ-01 (detection-predicate strength A vs B, and the grandfather cutoff) MUST be resolved by a human before E-01.
2. Scope fence: touch ONLY `check_engine.py` (the new rule), `doctor.py` (remediation), the tests, and the check-rule docs via managed verbs. Do NOT implement preventive gating (that is `9bd3j8` + ipdgates), and do NOT duplicate the ipdgates Order 07 or unifyfileio Order 05 checks. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via the tool (`aw ipd finalize` if available by then, else `aw ipd set executed`), append the `## Workflow history` line, move the plan, and make the path-scoped lifecycle commit.
