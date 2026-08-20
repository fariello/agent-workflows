# IPD: unify severity labels in Term (P14 bracketed fixed-width) + consistent machine-output flags

- Date: 2026-08-20
- Concern: ui-ux (CLI output UX): concise + colorful for human TTYs, machine-targeted for non-TTYs. Assessed via /assess ui-ux.
- Scope: `agent_workflows/term.py` (the shared label/color helper, 195 status call sites) + `agent_workflows/doctor.py` (private duplicate labels) + the machine-output flag surface on read verbs (`cli.py`) + a short output-conventions doc note. Does NOT restyle every line or add features; it unifies the existing severity-label convention and the non-TTY flag surface. Read-only assessment produced this plan; no code changed.
- Kind: child
- Status: to-review
- Set: awuiux
- Order: 1
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ygeuha

## Workflow history

- 2026-08-20 /assess ui-ux (opencode its_direct/pt3-claude-opus-4.8-1m-us): assessed; proposed 5 changes.

## Goal

Make the CLI's severity output consistent and scannable on a TTY (the P14 bracketed, fixed-width, bold-colored `[ERROR]`/`[WARN ]`/`[INFO ]` labels) by implementing that convention ONCE in the shared `Term` helper (today it is only hand-rolled in `doctor.py` while `Term` still emits bare variable-width words at 195 call sites), and give agents a UNIFORM machine-output flag across read verbs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: single-source the P14 severity labels in Term

- [ ] E-01 In `agent_workflows/term.py`, add the P14 bracketed fixed-width severity labels as the CANONICAL implementation: a helper (e.g. `severity_label(kind)`) returning `[ERROR]` (word bold red 196), `[WARN ]` (bold yellow 226), `[INFO ]` (bold green 46) with the WORD bold-colored, brackets uncolored, and the words padded so the brackets align (ERROR=5; WARN/INFO get a trailing space). Add `error`/`warn`/`info` entries to `_STATUS_STYLE` (or a parallel severity map) so `status("error", ...)`/`("warn",...)`/`("info",...)` route through it. Preserve monochrome/NO_COLOR honesty (the bracketed WORD is always present) and the existing `should_color` gating.
  - Depends on: none
  - Expected outcome: `Term(color=True).severity_label("error")` yields ANSI-bold-red `ERROR` inside plain `[...]`; `Term(color=False)` yields plain `[ERROR]`; `[WARN ]`/`[INFO ]` align to the same width.
  - Execution state: pending

- [ ] E-02 Make `doctor.py` consume the Term severity labels instead of its PRIVATE `_error`/`_warn`/`_info` helpers (doctor.py:25/30/35), deleting the duplicates (P8 single-source-of-truth). Verify `aw doctor` output is unchanged (still `[INFO ]`/`[WARN ]`/`[ERROR]` bracketed) but now sourced from Term.
  - Depends on: E-01
  - Expected outcome: `doctor.py` has no private bracket-label helpers; `aw doctor` still prints the identical bracketed labels, now via Term.
  - Execution state: pending

### Task group 2: align the general status labels (scannability)

- [ ] E-03 In `Term.status_label`/`status`, render the general status words (OK/FAIL/WARN/SKIP/STALE/CURRENT/NOT-INSTALLED/...) at a FIXED WIDTH (pad to the longest label, e.g. `NOT-INSTALLED`) so the message column aligns on a TTY (UX-002). Keep the word + color (color redundant). Do NOT change the machine/`--agent`/`--json` output (those must stay byte-stable); this padding is the human-TTY branch only. Confirm no test that asserts exact `status()` output breaks (update any that pin the unpadded form).
  - Depends on: E-01
  - Expected outcome: colored `aw list-repos` aligns the path column across STALE/CURRENT/NOT-INSTALLED rows; machine output unchanged.
  - Execution state: pending

### Task group 3: uniform non-TTY machine-output flag

- [ ] E-04 Standardize the machine-output flag on read verbs (UX-003): survey `check/find/search/index` (both --json + --agent), `attention`/`doctor` (only --agent), `status`/`list-repos` (only --json), `backlog check` (only --agent). Make `--json` the CANONICAL structured agent flag present on every machine-facing READ verb; add the missing one to the outliers (add `--json` to attention/doctor as an alias/format of their existing machine output; keep `--agent` tab-separated where the output is Drift-shaped). Update each verb's `--help` to state the non-TTY contract. Do NOT change the DEFAULT (human) output or the already-stable `--agent`/`--format json` payloads; this only fills the gaps so agents have one reliable flag.
  - Depends on: none
  - Expected outcome: every machine-facing read verb accepts `--json` and emits valid JSON; `--agent` still works where present; help documents the contract.
  - Execution state: pending

### Task group 4: tests + doc

- [ ] E-05 Add `tests/test_term_severity.py` asserting: severity_label bracketed fixed-width alignment (ERROR/WARN/INFO), color-on vs NO_COLOR (word always present, no ANSI when off), and status_label padding (E-03); assert `aw doctor` labels come from Term (no private helpers). Add/extend a machine-flag test asserting each targeted read verb emits valid JSON under `--json` (E-04). Add a short "output conventions" note (TTY concise+colored via Term; non-TTY `--json`/`--agent` machine) to CONTRIBUTING.md or the Term module docstring (UX-005), cross-referencing GUIDING_PRINCIPLES P14. Run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: new/updated tests pass; the output-conventions note exists; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Severity-label convention is GUIDING_PRINCIPLES P14: bracketed, fixed-width, WORD bold-colored ([ERROR] red / [WARN ] yellow / [INFO ] green), word always present for monochrome/NO_COLOR honesty.
- ALL colored output routes through `agent_workflows/term.py` `Term` (0 hand-rolled ANSI elsewhere) - so one helper change propagates to 195 `status()` call sites.
- `doctor.py:25/30/35` ALREADY hand-implements the P14 bracket labels privately; `Term.status_label`/`_STATUS_STYLE` (term.py:146) does NOT - it emits bare variable-width words. That divergence is the core finding.
- Color policy: `should_color` (term.py:56) honors NO_COLOR/FORCE_COLOR/TTY/--no-color; correct and must be preserved.
- Plans lifecycle: `.aw/records/plans/{pending,executed,superseded,not-executed,reusable}`; front-matter Status readiness; IPD born `to-review`. Framework dir + workflow-artifacts are out of assessment scope.

## Findings

| ID | Severity | Remediation Risk | Persona | Evidence | Finding |
|----|----------|------------------|---------|----------|---------|
| UX-001 | High | C:Low U:Low S:Low F:Low Overall:Low | power-user; UI/UX | term.py:146; doctor.py:25/30/35; GUIDING_PRINCIPLES P14 | P14 bracketed labels are hand-rolled in doctor.py but the canonical Term helper (195 sites) emits bare words - duplicate/divergent impl (P8). |
| UX-002 | Medium | Low (usability) | UI/UX; novice | live `aw list-repos` (STALE vs NOT-INSTALLED misalign) | Variable-width bare status words make the message column ragged; hurts TTY scannability. |
| UX-003 | Medium | Low (usability) | power-user; stakeholder | per-verb --help matrix | Non-TTY machine flags inconsistent: check/find/search/index have --json+--agent; attention/doctor only --agent; status/list-repos only --json - no uniform agent flag. |
| UX-004 | Low | Low (usability) | novice | `aw find plans --status nonexistent` -> `no matching plans` | Empty-state feedback is terse; could name the filter + suggest a next step. |
| UX-005 | Low | Low (complexity) | UI/UX | term.py:56 should_color; scattered color= | The TTY-vs-machine output contract is not documented in one place for contributors adding verbs. |

## Proposed changes (ordered, validatable)

1. Implement P14 severity labels once in Term (E-01).
2. Delete doctor's private duplicates, consume Term (E-02).
3. Fixed-width-align the general status labels on the TTY branch (E-03).
4. Add the uniform `--json` machine flag across read verbs (E-04).
5. Tests + output-conventions doc note (E-05).

## Deferred / out of scope (with reason)

- Restyling non-severity body text / tables / boards: not proposed (P14 is severity-class only; would be gold-plating).
- UX-004 (richer empty-state hints) is folded into E-04/E-05 lightly; a broader empty/loading/error-state pass across every verb is deferred (larger UX product decision - see open question) rather than expanded here.

## Scope check

- Over-scope: none - each change targets a found defect; no new features.
- Under-scope: does not touch accessibility (separate lens) or self-documentation/help-text quality (covered by the executed awhelp Set).

## Required tests / validation

`tests/test_term_severity.py` + a machine-flag JSON test; full serial suite green; `aw doctor` labels visually unchanged; `aw list-repos` columns aligned under FORCE_COLOR; machine output byte-stable.

## Spec / documentation sync

Add an "output conventions" note (CONTRIBUTING.md or Term docstring) cross-referencing GUIDING_PRINCIPLES P14 (E-05). No spec governs CLI cosmetics.

## Open questions

### OQ-01: Should empty/loading/error-state feedback be standardized across ALL verbs (a broader UX pass), or is the light touch here (E-04 help + UX-004 note) enough for now?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: This IPD does the high-value, low-risk unification (labels + machine flag). A full empty/loading/success/error-state audit across every verb is a larger UX product decision; deferred to the maintainer to scope as a follow-on if wanted, rather than expanded speculatively here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `Term(color=True).severity_label("error"/"warn"/"info")` returns bracketed labels with the WORD bold-colored (red196/yellow226/green46) and brackets uncolored, padded so ERROR/WARN/INFO brackets align; `Term(color=False)` returns plain `[ERROR]`/`[WARN ]`/`[INFO ]` with no ANSI. Shown by test_term_severity.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `doctor.py` has no private `_error`/`_warn`/`_info` bracket helpers (grep empty); `aw doctor` still prints identical `[INFO ]`/`[WARN ]`/`[ERROR]` labels, now sourced from Term.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: under FORCE_COLOR, `aw list-repos` aligns the path column across STALE/CURRENT/NOT-INSTALLED rows (fixed-width labels); `--agent`/`--json`/machine output byte-unchanged (diff before/after empty).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: every targeted read verb (check/find/search/index/attention/doctor/status/list-repos/backlog check) accepts `--json` and emits valid JSON (`json.loads` succeeds); `--agent` still works where present; `--help` states the contract.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_term_severity.py -p no:xdist -q` green; the output-conventions note exists (CONTRIBUTING.md or Term docstring, cross-refs P14); full serial suite tail pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST be human-approved (Status: approved) before execution; it is not auto-run. Execution contract: commit only files changed by the plan, path-scoped, never push; run the full serial suite and paste the ACTUAL runner output as V evidence; keep `--agent`/`--json` machine payloads byte-stable (human-TTY changes only); on completion lint --phase pre-transition while approved, then flip to executed + executed history + git mv to executed/ + post-transition lint. Do not mark executed until every V item is verified with concrete evidence.
