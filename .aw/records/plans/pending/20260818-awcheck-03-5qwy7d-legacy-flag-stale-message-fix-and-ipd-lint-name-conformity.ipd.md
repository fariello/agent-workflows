# IPD: legacy flag stale message fix and ipd lint name conformity

- Date: 2026-08-18
- Kind: child
- Concern: awcheck Order 03 (spec 20260818-1525-01; TODO items 6, 11, 20). Finish the check surface: (11) fix the stale message "All scanned plan/prompt filenames conform to YYYYMMDD-HHMM-NN-<slug>.md." (normalize_plan_names.py:677) which advertises the OLD grammar; (20) give the check engine a `--legacy` behavior so legacy-named files pass without findings; (6) make `aw ipd lint` also verify filename conformity via the engine's name check. Small, targeted edits building on the Order-01 engine.
- Scope: `.aw/system/workflows/setup-repo/tools/normalize_plan_names.py` (message), `agent_workflows/check_engine.py` (legacy behavior in check_names), `agent_workflows/ipd_lint.py` (call name conformity), + test updates. IN: correct + grammar-accurate message honoring legacy; `check_names(..., legacy=True)` treats a legacy `YYYYMMDD-HHMM-NN-<slug>.md` name as conformant (no drift); `aw ipd lint` emits a name-conformity diagnostic for a nonconformant plan filename. OUT: the engine core (Order 01) + collisions (Order 02); CLI verb wiring for `aw check` (awcmdsurf).
- Status: approved
- Approval: 2026-08-18, human ("Approve ALL 21 IPDs now ... Execute everything one at a time using Gemini ... then do it yourself.") after /plan-review (rigorous, opencode Opus 4.8; APPROVE / APPROVE WITH REVISIONS APPLIED).
- Set: awcheck
- Order: 3
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 5qwy7d

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from investigation (stale message normalize_plan_names.py:677; is_conformant expected_type normalize_plan_names.py:205; ipd_lint.run_lint legacy flag ipd_lint.py:767; _NEW_RE legacy grammar already faceted).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against normalize_plan_names.py:677, ipd_lint.py:761-770, and check_engine.py:check_names; structural lint conforming; no findings; no open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE; re-review (opencode): verified stale message:677, run_lint/legacy:761-768; conforming; no findings.
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. Ran the live normalizer. PR-001 (MEDIUM): E-02/E-04/F2 used `20260101-1200-01-old-style.md` (HHMM-NN) as the "flagged without legacy" fixture, but that form is ALREADY is_conformant==True (accepted by _NEW_RE), so it is never flagged and the built test would FAIL. The legacy flag's mechanism is correct, but its exemplar was wrong; switched the fixture to a hyphenated-date legacy name `2026-01-01-<slug>.md` (is_conformant False, parse_name non-None), which actually exercises the flag. Stale-message fix (E-01), run_lint --legacy/terminal-short-circuit (E-03) verified accurate. Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.

## Goal

Close the three remaining name-check gaps: replace the stale conform message with a grammar-accurate one
that respects a legacy allowance; make the check engine's name check treat legacy-named files as
conformant when `legacy=True`; and have `aw ipd lint` surface a filename-nonconformity diagnostic so a
badly-named IPD is caught by lint too.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Order 01 (`check_engine.py` with `check_names`) MUST be present. Make ONLY the edits
below at the exact anchors. Return Drift / diagnostics; keep changes minimal.

### Task group 1: fix the stale message (item 11)

- [ ] E-01 In `.aw/system/workflows/setup-repo/tools/normalize_plan_names.py`, replace the stale success message at line 677. Change the exact string `"All scanned plan/prompt filenames conform to YYYYMMDD-HHMM-NN-<slug>.md."` to `"All scanned filenames conform to the naming grammar (YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md; the legacy YYYYMMDD-HHMM-NN-<slug>.md form is also accepted)."`. This is a one-line string change; do not alter the surrounding logic.
  - Depends on: none
  - Expected outcome: a clean `aw plan-names` (or the engine names check) run prints the grammar-accurate message, not the old-only one.
  - Execution state: pending

### Task group 2: legacy allowance in the engine name check (item 20)

- [ ] E-02 In `agent_workflows/check_engine.py`, make `check_names(repo_root, record_type, legacy=False)` honor `legacy`: when `legacy=True`, a filename that is NOT conformant to the CURRENT grammar but IS a recognized legacy shape (the normalizer's `parse_name(name)` returns a non-None Parsed) is treated as OK (no drift). Concretely: if `is_conformant(name, expected_type=<facet>)` is False, THEN if `legacy` and `parse_name(name) is not None`, skip (no drift); else emit the `check.name-nonconformant` Drift. (parse_name is in the same shipped normalizer module loaded in Order 01.) IMPORTANT (verified empirically against the live normalizer): the classic `YYYYMMDD-HHMM-NN-<slug>.md` form is ALREADY `is_conformant==True` (accepted by `_NEW_RE`), so it is NEVER flagged and the legacy flag has no effect on it. The shape the flag actually governs is one that FAILS `is_conformant` but `parse_name` still recognizes - e.g. the hyphenated-date legacy form `2026-01-01-<slug>.md` (is_conformant False, parse_name non-None). Use THAT as the test fixture, not the HHMM-NN form.
  - Depends on: none
  - Expected outcome: over a fixture with a hyphenated-date legacy plan `2026-01-01-old-hyphenated.md` (is_conformant False, parse_name non-None): `check_names(root,"plans")` (no legacy) flags it with `check.name-nonconformant`; `check_names(root,"plans",legacy=True)` does NOT. (A `YYYYMMDD-HHMM-NN` name would NOT be flagged even without legacy, since it is already conformant - do not use it as the fixture.)
  - Execution state: pending

### Task group 3: ipd lint checks the filename (item 6)

- [ ] E-03 In `agent_workflows/ipd_lint.py`, make `run_lint` (ipd_lint.py:761) ALSO check the linted file's NAME conformity. After computing the structural result for a file, call the engine's name conformity for a single filename: add a small helper `_name_conformant(path, legacy)` in ipd_lint.py that loads the shipped normalizer (same loader pattern as check_engine) and returns whether `path.name` is conformant as an `ipd` (respecting `legacy` like E-02). If NOT conformant, add a diagnostic `IPD-N001` "filename does not match the plan grammar (YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md)" to the file's diagnostics BEFORE deciding the exit code, so a badly-named IPD lints as an error (unless `--legacy`). Keep the existing structural checks intact; this is an ADDITIONAL diagnostic. Do NOT change the terminal-dir short-circuit behavior (a terminal-dir file without --legacy is still not-evaluated).
  - Depends on: none
  - Expected outcome: `aw ipd lint <a plan file whose name violates the grammar>` reports IPD-N001 and returns 1; a well-named plan is unaffected; `--legacy` suppresses IPD-N001 for a legacy name.
  - Execution state: pending

### Task group 4: tests

- [ ] E-04 Update tests: (a) add to `tests/test_check_engine.py` a `LegacyNamesTests` with `test_legacy_flag_allows_legacy_name` (a HYPHENATED-DATE legacy plan `2026-01-01-old-hyphenated.md` - which fails is_conformant but parse_name recognizes - is flagged WITHOUT legacy, allowed WITH legacy; do NOT use a `YYYYMMDD-HHMM-NN` name, which is already conformant and would make the "flagged without legacy" assertion fail) and `test_current_name_ok` (a conformant `.ipd.md` name never flagged). (b) add to the ipd-lint tests (find the existing ipd lint test file, e.g. `tests/test_ipd_lint.py`) a test that a grammar-violating filename (again a hyphenated-date or garbage name, NOT HHMM-NN) yields IPD-N001 and `--legacy` suppresses it for the parse_name-recognized legacy shape. (c) if any existing test asserted the OLD stale message string, update it to the new message. Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: the new tests pass; any message-asserting test updated; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Stale message is a single print at normalize_plan_names.py:677 (grammar text is wrong/old).
- `is_conformant(name, expected_type=...)` (normalize_plan_names.py:205) validates the current grammar incl. the `.type.md` facet AND (verified empirically) already accepts the `YYYYMMDD-HHMM-NN-<slug>` legacy form via `_NEW_RE` (so that form is conformant, NOT flagged, with or without legacy). `parse_name` (normalize_plan_names.py:171) returns a Parsed (whose `conformant` bool is True even for the HHMM-NN form) or None. The names that FAIL is_conformant yet parse_name recognizes (so the legacy flag matters) are the OTHER legacy shapes, e.g. hyphenated-date `2026-01-01-<slug>.md` (is_conformant False, parse_name non-None) and true garbage (both False -> flagged even under legacy).
- `aw ipd lint` ALREADY has a `--legacy` flag (ipd_lint.py:767) and a terminal-dir short-circuit; the new IPD-N001 diagnostic must respect both.
- The engine's `check_names` (Order 01) already accepts a `legacy` passthrough; this Order gives it behavior.
- Facet per type: plans->ipd, specs->spec, backlog->backlog, prompts->prompt, walkthroughs->walkthrough, roadmaps->roadmap (research excepted).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | The stale message is one line. | Trivial, high-value fix (item 11). |
| F2 | parse_name distinguishes legacy from unknown; but the HHMM-NN form is ALREADY is_conformant. | `legacy=True` allows names that FAIL is_conformant yet parse_name recognizes (e.g. hyphenated-date `2026-01-01-...`). The HHMM-NN form is conformant regardless, so it must NOT be the legacy-flag fixture (verified empirically; earlier draft used it wrongly -> a failing test). |
| F3 | ipd lint already has --legacy + terminal short-circuit. | IPD-N001 slots in respecting both; no behavior regression. |

## Proposed changes (ordered, validatable)

1. Fix stale message (E-01). 2. `legacy` behavior in `check_names` (E-02). 3. IPD-N001 filename check in `run_lint` (E-03). 4. Tests + suite (E-04).

## Deferred / out of scope (with reason)

- Engine core (Order 01) + collisions (Order 02): done. CLI `aw check` verb: awcmdsurf.
- A repo-wide `--legacy` flag on the CLI verbs: that surfaces when awcmdsurf wires `aw check --legacy`; the engine behavior lands here.

## Scope check

- Over-scope: none - message + legacy behavior + ipd-lint name check.
- Under-scope: none - items 6, 11, 20 all addressed with tests.

## Required tests / validation

`tests/test_check_engine.py::LegacyNamesTests` + an ipd-lint filename test + the full serial suite (E-04). Each V pins one E.

## Spec / documentation sync

Message text corrected (E-01). No AGENTS.md change. No spec transition (orchestrator advances the spec).

## Open questions

### OQ-01: should IPD-N001 be an error or a warning-level diagnostic?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: ERROR (returns 1), consistent with lint's other structural findings, UNLESS `--legacy` (then suppressed for a legacy-shaped name). A badly-named NEW IPD should fail lint so it is fixed before execution. Resolved per E-03.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new grammar-accurate message from a clean names run (the old "YYYYMMDD-HHMM-NN-<slug>.md"-only string is gone).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `check_names` flagging a HYPHENATED-DATE legacy plan (`2026-01-01-old-hyphenated.md`, which fails is_conformant but parse_name recognizes) WITHOUT legacy, and NOT flagging it WITH `legacy=True`; also show a `YYYYMMDD-HHMM-NN` name is not flagged either way (already conformant), confirming the fixture choice.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `aw ipd lint <badly-named plan>` reporting IPD-N001 (exit 1) and `--legacy` suppressing it for a legacy name; a well-named plan unaffected.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the new tests passing + the full serial suite tail (no regressions).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the four touched
files path-scoped (never `git add -A`), never pushes, and transitions only after `aw ipd lint --phase
pre-transition` conforms and every V is `pass`. Terminal Order of awcheck; depends on Order 01 (engine).
On Set completion the orchestrator advances spec 20260818-1525-01 accordingly (jointly with awcmdsurf).
