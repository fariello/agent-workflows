# IPD: legacy flag stale message fix and ipd lint name conformity

- Date: 2026-08-18
- Kind: child
- Concern: awcheck Order 03 (spec 20260818-1525-01; TODO items 6, 11, 20). Finish the check surface: (11) fix the stale message "All scanned plan/prompt filenames conform to YYYYMMDD-HHMM-NN-<slug>.md." (normalize_plan_names.py:677) which advertises the OLD grammar; (20) give the check engine a `--legacy` behavior so legacy-named files pass without findings; (6) make `aw ipd lint` also verify filename conformity via the engine's name check. Small, targeted edits building on the Order-01 engine.
- Scope: `.aw/system/workflows/setup-repo/tools/normalize_plan_names.py` (message), `agent_workflows/check_engine.py` (legacy behavior in check_names), `agent_workflows/ipd_lint.py` (call name conformity), + test updates. IN: correct + grammar-accurate message honoring legacy; `check_names(..., legacy=True)` treats a legacy `YYYYMMDD-HHMM-NN-<slug>.md` name as conformant (no drift); `aw ipd lint` emits a name-conformity diagnostic for a nonconformant plan filename. OUT: the engine core (Order 01) + collisions (Order 02); CLI verb wiring for `aw check` (awcmdsurf).
- Status: to-review
- Set: awcheck
- Order: 3
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 5qwy7d

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from investigation (stale message normalize_plan_names.py:677; is_conformant expected_type normalize_plan_names.py:205; ipd_lint.run_lint legacy flag ipd_lint.py:767; _NEW_RE legacy grammar already faceted).

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

- [ ] E-02 In `agent_workflows/check_engine.py`, make `check_names(repo_root, record_type, legacy=False)` honor `legacy`: when `legacy=True`, a filename that is NOT conformant to the CURRENT grammar but IS a recognized LEGACY name (the normalizer's `parse_name(name)` returns a non-None Parsed whose `conformant` is False but which parses as a legacy shape) is treated as OK (no drift). Concretely: if `is_conformant(name, expected_type=<facet>)` is False, THEN if `legacy` and `parse_name(name) is not None`, skip (no drift); else emit the `check.name-nonconformant` Drift. (parse_name is in the same shipped normalizer module loaded in Order 01.)
  - Depends on: none
  - Expected outcome: over a fixture with a legacy-named plan `20260101-1200-01-old-style.md`: `check_names(root,"plans")` (no legacy) flags it; `check_names(root,"plans",legacy=True)` does NOT.
  - Execution state: pending

### Task group 3: ipd lint checks the filename (item 6)

- [ ] E-03 In `agent_workflows/ipd_lint.py`, make `run_lint` (ipd_lint.py:761) ALSO check the linted file's NAME conformity. After computing the structural result for a file, call the engine's name conformity for a single filename: add a small helper `_name_conformant(path, legacy)` in ipd_lint.py that loads the shipped normalizer (same loader pattern as check_engine) and returns whether `path.name` is conformant as an `ipd` (respecting `legacy` like E-02). If NOT conformant, add a diagnostic `IPD-N001` "filename does not match the plan grammar (YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md)" to the file's diagnostics BEFORE deciding the exit code, so a badly-named IPD lints as an error (unless `--legacy`). Keep the existing structural checks intact; this is an ADDITIONAL diagnostic. Do NOT change the terminal-dir short-circuit behavior (a terminal-dir file without --legacy is still not-evaluated).
  - Depends on: none
  - Expected outcome: `aw ipd lint <a plan file whose name violates the grammar>` reports IPD-N001 and returns 1; a well-named plan is unaffected; `--legacy` suppresses IPD-N001 for a legacy name.
  - Execution state: pending

### Task group 4: tests

- [ ] E-04 Update tests: (a) add to `tests/test_check_engine.py` a `LegacyNamesTests` with `test_legacy_flag_allows_legacy_name` (legacy-named plan flagged without legacy, allowed with legacy) and `test_current_name_ok` (a conformant `.ipd.md` name never flagged). (b) add to the ipd-lint tests (find the existing ipd lint test file, e.g. `tests/test_ipd_lint.py`) a test that a grammar-violating filename yields IPD-N001 and `--legacy` suppresses it. (c) if any existing test asserted the OLD stale message string, update it to the new message. Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: the new tests pass; any message-asserting test updated; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Stale message is a single print at normalize_plan_names.py:677 (grammar text is wrong/old).
- `is_conformant(name, expected_type=...)` (normalize_plan_names.py:205) already validates the current grammar incl. the `.type.md` facet; `parse_name` (normalize_plan_names.py:171) returns a Parsed (with a `conformant` bool) or None; a legacy `YYYYMMDD-HHMM-NN-<slug>` parses (non-None) but is not "conformant" to the clustered grammar.
- `aw ipd lint` ALREADY has a `--legacy` flag (ipd_lint.py:767) and a terminal-dir short-circuit; the new IPD-N001 diagnostic must respect both.
- The engine's `check_names` (Order 01) already accepts a `legacy` passthrough; this Order gives it behavior.
- Facet per type: plans->ipd, specs->spec, backlog->backlog, prompts->prompt, walkthroughs->walkthrough, roadmaps->roadmap (research excepted).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | The stale message is one line. | Trivial, high-value fix (item 11). |
| F2 | parse_name distinguishes legacy from unknown. | `legacy=True` = "parses as a known legacy shape" -> allow; unknown -> still flag. Deterministic. |
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
  - Required evidence: paste `check_names` flagging a legacy-named plan without legacy and NOT flagging it with `legacy=True`.
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
