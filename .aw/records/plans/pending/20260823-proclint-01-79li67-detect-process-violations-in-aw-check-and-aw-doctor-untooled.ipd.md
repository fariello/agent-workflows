# IPD: Detect process violations in aw check and aw doctor (untooled status changes, unattributed transitions)

- Date: 2026-08-23
- Kind: child
- Concern: This toolkit requires lifecycle status to change via `aw set`/`aw ipd set` (which append an attributed `## Workflow history` line), not by hand-editing the `- Status:` field - but that is enforced only by soft prose in AGENTS.md and is consistently dropped by ALL current agents (cross-vendor, observed repeatedly - including a reviewer that hand-edited `- Status:` on several plans in this repo). The `ipdgates` Set gates the high-stakes TERMINAL transition (a plan -> `executed`, via finalize + Order 07 delegation + Order 08's pre-commit receipt gate). Nothing catches a hand-edited INTERMEDIATE transition (`draft`->`to-review`->`reviewed`->`approved`), and `approved` is a trust boundary. This IPD adds a COMMIT-SCOPED detector for that gap: when a commit changes a plan's `- Status:` with no matching tool-authored history line, flag it - so the careless untooled intermediate transition becomes visible.
- Scope: Add a deterministic, COMMIT-SCOPED check (over the STAGED/changed files in the commit, NOT a scan of the whole tree) that flags a plan whose `- Status:` changed in this commit without a matching tool-authored `## Workflow history` transition line, surfaced through `aw check` (over changed files) and, primarily, a local pre-commit hook - the intermediate-transition sibling of ipdgates Order 08. `executed/` records are EXCLUDED (terminal/immutable; a plan moved OUT of `executed/` is itself a staged change and IS checked). Touch: agent_workflows/check_engine.py (the changed-file status-vs-history rule), a local pre-commit hook + its `.pre-commit-config.yaml` wiring (mirroring Order 08's pattern), agent_workflows/doctor.py (remediation mapping), and tests. Explicitly does NOT re-implement the id6-identity-slot check (unifyfileio Order 05 `9a655p`), the terminal-history generic-actor lint (ipdgates Order 07 `wezhxg`), or the terminal executed-transition gate (ipdgates Order 08 `dulzpy`); it covers the DISTINCT "an INTERMEDIATE status changed in THIS commit with no tool-authored transition line" violation. NO grandfathering (unchanged/historical records are never examined) and NO GitHub CI (local only, mirroring Order 08's human decision).
- Status: approved
- Set: proclint
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 79li67
- Approval: 2026-08-24, human ("approved. go."): status set to approved

## Workflow history
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-24 reviewed (aw set): plan-review self-review (author); commit-scoped rescope + predicate A applied - see workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created at maintainer direction, as the DETECTIVE counterpart to research prompt `9bd3j8` (preventive/how-to-make-adherence-stick) - "aw check/aw doctor should flag things done improperly if possible."
- 2026-08-23 reviewed (Antigravity): plan-review completed; clarified detection predicate, grandfather heuristic, and doctor remediation mapping; set to-review per human instruction.
- 2026-08-24 /plan-review SELF-REVIEW (opencode its_direct/pt3-claude-opus-4.8-1m-us - NOTE: same agent that AUTHORED this plan; an independent reviewer is preferable): APPROVE WITH REVISIONS APPLIED. Material RESCOPE at human direction: from a repo-SCANNING `aw check`/`aw doctor` rule with grandfathering to a COMMIT-SCOPED check (staged-vs-HEAD, only files changed in the commit), which excludes `executed/` and ELIMINATES all grandfather/cutoff machinery (historical records are never examined). PR-001 (stated the EFFICACY CEILING honestly - predicate A catches only careless omission, is evadable, not "prevents/proves"); PR-002 (made the prompts/releases COVERAGE GAP explicit - history-less types can't be covered); OQ-01 human-resolved = predicate A (textual; option B signed-marker rejected as disproportionate) and the grandfather sub-question DISSOLVED by commit-scoping. Positioned as the INTERMEDIATE-transition sibling of ipdgates Order 08 (which gates the terminal `->executed`), local only / no CI. Verified `aw set` history-line behavior (`status_set.py:462-479`), the `_HISTORY_LINE_RE` status-only capture (`ipd_lint.py:168`), and that prompts/releases carry no `## Workflow history`.

## Goal

Give a local, COMMIT-SCOPED check a way to catch the CARELESS untooled INTERMEDIATE status change: a plan whose `- Status:` was changed in THIS commit by hand (or any non-`aw` path) with no matching `## Workflow history` transition line for that status. `aw set`/`aw ipd set` append `- <date> <status> (<actor>): <message>` on every transition for history-bearing types (`status_set.py:463`); a staged status change with no such matching line is the fingerprint of a careless hand-edit. Flag it with an actionable remediation ("this status change looks hand-edited; apply it via `aw set <status> <id>` so it is attributed"). Inspect ONLY the files changed in the commit (so unchanged/historical records are never examined - no grandfathering needed), EXCLUDE `executed/` (terminal; a move OUT of `executed/` is a staged change and is checked), and do not fire on types with no `## Workflow history` (prompts/releases - see the coverage gap).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The commit-scoped status-vs-history consistency check

- [ ] E-01 In `agent_workflows/check_engine.py`, add a COMMIT-SCOPED rule (e.g. `check.status-untooled`) that, given the set of PLAN files whose `- Status:` changed in the commit (compare staged content vs HEAD; ignore files not in the commit and files under `executed/`), flags each whose new status has NO matching tool-authored `## Workflow history` transition line for that status value (predicate A per OQ-01: a plain textual "is there a matching `- <date> <status> (...)` line" check - catches the careless omission, does NOT catch a hand-edit that also adds a plausible line; that limit is accepted). Reuse `ipd_lint`'s `_HISTORY_LINE_RE`/`doc.history_lines` parsing (`ipd_lint.py:168`) rather than a second parser. Fire fail-closed with the standard `Drift`/exit convention. NO grandfathering and NO whole-tree scan (only commit-changed files are examined, so historical records are never touched). Restrict to history-bearing plan records; do not examine prompts/releases (no `## Workflow history`).
  - Depends on: none
  - Expected outcome: for a commit that hand-changes a plan's `- Status:` with no matching history line, the check flags it; a commit that changed status via `aw set` (matching attributed line present) is clean; files not changed in the commit and `executed/` records are never examined.
  - Execution state: pending

### Task group 2: Wire it as a local pre-commit hook + doctor remediation

- [ ] E-02 Register the E-01 check as a LOCAL `repo: local` pre-commit hook in `.pre-commit-config.yaml` (mirroring ipdgates Order 08's pattern and the existing local-leaks guard), scoped to the staged plan files, running once per commit and a fast no-op when no plan status change is staged; and map the rule into `agent_workflows/doctor.py` so `aw doctor` (over changed files) reports it with a self-documenting remediation naming the exact fix ("apply this status change via `aw set <status> <id6>` so it carries an attributed history entry"). Do NOT add any GitHub Actions / CI (local only, per Order 08's human decision).
  - Depends on: E-01
  - Expected outcome: a raw `git commit` of a hand-edited intermediate status change is flagged locally with an actionable remediation; a fresh install gets the hook; no CI workflow is added; a commit with no plan status change is a fast no-op.
  - Execution state: pending

### Task group 3: Prove detection + no false positives + no whole-tree scan

- [ ] E-03 Add tests: a fixture staging a hand-edited `- Status:` change (no matching tool-authored line) is FLAGGED; a fixture whose status change was made via `aw set` (matching attributed line) is CLEAN; an UNCHANGED plan with a historically hand-set status is NOT examined (proving commit-scoping, not a tree scan - no grandfathering needed); a plan moved OUT of `executed/` IS checked; a plan inside `executed/` is NOT; a prompt/release (no `## Workflow history`) is not falsely flagged; an ordinary commit with no plan status change is a fast no-op. Confirm `pytest -n auto` is green. No network/CI test.
  - Depends on: E-01, E-02
  - Expected outcome: the careless hand-edit is caught in-commit, the tooled path is clean, and commit-scoping (unchanged tree ignored, executed/ excluded, history-less types excluded) is proven - no false positives, no whole-tree scan.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw set`/`aw ipd set` append `- <date> <status> (<actor>): <message>` to `## Workflow history` on every transition for history-bearing types (`status_set.py:462-479`); the generic default actor is `aw set` (`status_set.py:356`). A hand-edited `- Status:` produces NO such line - that asymmetry is the detection signal.
- `check_engine.py` composes per-type `Drift` rules consumed by `aw check`; `doctor.py` maps rules to remediations; `.pre-commit-config.yaml` already has a `repo: local` hook invoking packaged `agent_workflows` (the local-leaks guard) - reuse that hook pattern.
- Commit-scoping (compare staged vs HEAD, inspect only changed files) is what removes the need for any grandfather/cutoff machinery: historical records are never examined, so they can never be retroactively flagged.
- Cross-references (do NOT duplicate): ipdgates Order 08 (`dulzpy`) gates the TERMINAL `->executed` transition at commit; Order 07 (`wezhxg`) the terminal-history generic-actor lint; unifyfileio Order 05 (`9a655p`) the id6-identity-slot check. THIS covers the INTERMEDIATE status transitions (`->to-review/->reviewed/->approved`) none of them gate.
- `aw set` writes the history line only for types that HAVE a `## Workflow history` section (plans, specs, backlog). Prompts and releases carry none, so this history-based signal cannot cover them.

## Findings

Soft prose enforcement of "use `aw set`" is not working across any agent; a deterministic, commit-scoped detector converts the invisible careless bypass into a visible, actionable finding at the moment it is committed. Commit-scoping is the key simplification: by examining only the files a commit changes, the detector needs NO grandfathering (the ~300 historical records are never looked at) and naturally excludes `executed/` (you are not changing them; a move OUT is itself a staged change and is checked). Detection is a safety net, not prevention; the preventive layer (hard gates / delegation / hooks) is research prompt `9bd3j8` + the `ipdgates` Set.

EFFICACY CEILING (state honestly, do not oversell): under the textual predicate (OQ-01 option A, human-chosen), this catches ONLY the CARELESS hand-edit - status changed with NO matching history line added. It does NOT catch a status hand-edit accompanied by a plausible hand-written `- <date> <status> (someactor): ...` line, because the history parser (`ipd_lint._HISTORY_LINE_RE`) sees only the STATUS token, not proof of tool-authorship. So it SURFACES the common omission (its real value) but is EVADABLE by a careful hand-edit; a tool-written signature (rejected option B) would be the only way to raise that ceiling, at a format/migration cost not justified for a safety-net detector. Do not claim it "prevents" or "proves" untooled changes.

COVERAGE GAP (verified): prompts and releases carry no `## Workflow history`, so a tooled status change leaves no line there; this detector cannot distinguish tooled from hand-edited status for them and excludes them. Prompts/releases are NOT protected by this check; separate future work if needed.

## Proposed changes (ordered, validatable)

1. Add the commit-scoped `check.status-untooled` rule (staged-vs-HEAD, changed plan files only, executed/ excluded, predicate A, no grandfathering) to `check_engine.py` (E-01).
2. Wire it as a local pre-commit hook + a self-documenting `aw doctor` remediation; no CI (E-02).
3. Tests: hand-edit flagged, tooled clean, unchanged-tree-ignored, executed/-excluded, moved-out-of-executed checked, history-less types clean, ordinary-commit no-op (E-03).

## Deferred / out of scope (with reason)

- The PREVENTIVE layer (hard gates, `aw set` delegation, host hooks): research prompt `9bd3j8` + the `ipdgates` Set; this IPD is detection only.
- The TERMINAL `->executed` gate: ipdgates Order 08 (`dulzpy`); the generic-actor terminal lint: Order 07 (`wezhxg`); id6-identity-slot: unifyfileio Order 05 (`9a655p`) - cross-referenced, not duplicated.
- Catching a hand-edit that ALSO adds a plausible history line (option B, a tool-written signature): out of scope - predicate A (careless-omission only) chosen by human as sufficient for a safety net; option B's format change + migration is not justified here.
- Prompts/releases (history-less types): excluded (coverage gap above).
- Whole-tree / historical scanning and any grandfather/cutoff machinery: explicitly OUT - the check is commit-scoped, so historical records are never examined.
- Non-status process violations (out-of-scope commits, missing IPD before coding): future proclint children pending `9bd3j8`.

## Scope check

- Over-scope: none. One commit-scoped detection rule + a local hook + a doctor remediation + tests. No CI, no tree scan, no grandfathering.
- Under-scope (known, accepted gaps - NOT silent): (a) history-less types (prompts/releases) are excluded; (b) a status hand-edit that ALSO adds a plausible history line is not caught (predicate A); (c) the TERMINAL transition is Order 08's job, not duplicated here. These are documented limits, not missing required capability for this detector's stated concern (the careless untooled INTERMEDIATE status change, caught in-commit).

## Required tests / validation

- Tests per E-03 (hand-edit flagged; tooled clean; unchanged tree not examined; executed/ excluded; moved-out-of-executed checked; history-less types clean; ordinary-commit no-op).
- Full suite via `pytest -n auto` (paste actual runner output). No network/CI test.

## Spec / documentation sync

- Document the new `check.status-untooled` rule + local hook in the check-rule list / `aw check`/`aw doctor` help and the lifecycle/installer docs (via managed verbs): it is a COMMIT-SCOPED DETECTOR for intermediate hand-edited status (the terminal gate is ipdgates Order 08; the preventive path is `aw set`); local only, no CI. Note `--no-verify` bypasses the hook (honest limit). Else N/A with reason.

## Open questions

### OQ-01: Detection predicate strength (textual vs signed)?

- Blocking: no
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-24, /plan-review): PREDICATE A (textual match) - flag a staged status change with no matching `- <date> <status> (...)` history line at all. Catches the actual observed failure (careless hand-edit, no note added); needs no change to `aw set`'s output format and no migration; honestly evadable by a careful hand-edit that adds a plausible line (accepted, because this is a safety net and the preventive layer is the separate ipdgates gates + `9bd3j8`). Option B (a tool-written tamper-evident signature) was REJECTED as disproportionate for a safety-net detector. The grandfather/cutoff sub-question is DISSOLVED: the check is COMMIT-SCOPED (only files changed in the commit are examined, `executed/` excluded), so historical records are never inspected and no grandfathering is needed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a unit test drives the check on a staged commit that changes a plan's `- Status:` with NO matching tool-authored history line and asserts a `check.status-untooled` Drift; a staged change made via `aw set` (matching attributed line) yields none; an UNCHANGED plan with a historically hand-set status is NOT examined (commit-scoping proven, no grandfather needed); a plan inside `executed/` is NOT checked while a plan moved OUT of `executed/` IS; a history-less type (prompt/release) yields none.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the hook is present in `.pre-commit-config.yaml` as a `repo: local` entry scoped to plan paths; a real `git commit` hand-editing an intermediate status is flagged, and one done via `aw set` passes; `aw doctor` renders the rule with a remediation naming `aw set <status> <id>`; a fresh `aw install`/setup-repo writes the hook; NO GitHub Actions/CI workflow was added (shown by absence); an ordinary commit with no status change is a fast no-op.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the full commit-scoped test set (hand-edit flagged, tooled clean, unchanged-tree-ignored, executed/-excluded, moved-out-of-executed checked, history-less clean, ordinary-commit no-op) passes and `pytest -n auto` is green (pasted); no network/CI test introduced.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - a commit-scoped detector for careless untooled INTERMEDIATE status changes, surfaced via a local pre-commit hook + `aw check`/`aw doctor`, distinct from ipdgates Order 08's terminal gate.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved by human (2026-08-24) - predicate A (textual, careless-omission only); commit-scoped so no grandfather/cutoff is needed. No blocking OQ remains.
2. Scope fence: touch ONLY `check_engine.py` (the commit-scoped rule), the local pre-commit hook + `.pre-commit-config.yaml` wiring + installer path that writes it, `doctor.py` (remediation), the tests, and the check-rule/lifecycle docs via managed verbs. Do NOT scan the whole tree, do NOT add grandfather/cutoff machinery, do NOT add GitHub Actions/CI, do NOT duplicate the ipdgates Order 07/08 or unifyfileio Order 05 checks, and do NOT implement preventive gating. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command. Do NOT claim the check is unbypassable - it is local best-effort (predicate A is evadable; `--no-verify` bypasses the hook).
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via the tool (`aw ipd finalize` if available by then, else `aw ipd set executed`), append the `## Workflow history` line, move the plan, and make the path-scoped lifecycle commit.
