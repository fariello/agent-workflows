# IPD: unify severity labels in Term (P14 bracketed fixed-width) + consistent machine-output flags

- Date: 2026-08-20
- Concern: ui-ux (CLI output UX): concise + colorful for human TTYs, machine-targeted for non-TTYs. Assessed via /assess ui-ux.
- Scope: `agent_workflows/term.py` (the shared label/color helper, 195 status call sites) + `agent_workflows/doctor.py` (private duplicate labels) + the machine-output flag surface on read verbs (`cli.py`) + a short output-conventions doc note. Does NOT restyle every line or add features; it unifies the existing severity-label convention and the non-TTY flag surface. Read-only assessment produced this plan; no code changed.
- Kind: child
- Status: executed
- Set: awuiux
- Order: 1
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ygeuha

## Workflow history

- 2026-08-20 /assess ui-ux (opencode its_direct/pt3-claude-opus-4.8-1m-us): assessed; proposed 5 changes.
- 2026-08-20 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed; OQ-01 resolved out-of-scope (release-blocking backlog oijafw filed), OQ-02 resolved (standardize --agent flag name, per-verb format).
- 2026-08-20 approved (maintainer, human): cleared for execution.
- 2026-08-20 executed (agy gemini exec + opencode independent validation): all E-01..E-05 implemented in commit dd1b964; V-01..V-05 independently verified (full serial suite 1243 passed, 1 skipped; sanitize clean; attention valid). agy reported status ERROR (known false-error, backlog uhbdt1: write_to_file sandbox rejected the new test path) but the work committed cleanly; validated against actual repo state.

## Goal

Make the CLI's severity output consistent and scannable on a TTY (the P14 bracketed, fixed-width, bold-colored `[ERROR]`/`[WARN ]`/`[INFO ]` labels) by implementing that convention ONCE in the shared `Term` helper (today it is only hand-rolled in `doctor.py` while `Term` still emits bare variable-width words at 195 call sites), and give agents a UNIFORM machine-output flag across read verbs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: single-source the P14 severity labels in Term

- [x] E-01 In `agent_workflows/term.py`, add the P14 bracketed fixed-width severity labels as the CANONICAL implementation: a helper (e.g. `severity_label(kind)`) returning `[ERROR]` (word bold red 196), `[WARN ]` (bold yellow 226), `[INFO ]` (bold green 46) with the WORD bold-colored, brackets uncolored, and the words padded so the brackets align (ERROR=5; WARN/INFO get a trailing space). Add `error`/`warn`/`info` entries to `_STATUS_STYLE` (or a parallel severity map) so `status("error", ...)`/`("warn",...)`/`("info",...)` route through it. Preserve monochrome/NO_COLOR honesty (the bracketed WORD is always present) and the existing `should_color` gating.
  - Depends on: none
  - Expected outcome: `Term(color=True).severity_label("error")` yields ANSI-bold-red `ERROR` inside plain `[...]`; `Term(color=False)` yields plain `[ERROR]`; `[WARN ]`/`[INFO ]` align to the same width.
  - Execution state: performed

- [x] E-02 Make `doctor.py` consume the Term severity labels instead of its PRIVATE `tag_error`/`tag_warn`/`tag_info` helpers (doctor.py:24/29/34; each takes a `term` and returns `[ERROR]`/`[WARN ]`/`[INFO ]` via `term.color256`), deleting the duplicates (P8 single-source-of-truth). Repoint every caller of `tag_error`/`tag_warn`/`tag_info` in doctor.py to the new Term helper. Verify `aw doctor` output is unchanged (still `[INFO ]`/`[WARN ]`/`[ERROR]` bracketed) but now sourced from Term.
  - Depends on: E-01
  - Expected outcome: `doctor.py` has no private bracket-label helpers; `aw doctor` still prints the identical bracketed labels, now via Term.
  - Execution state: performed

### Task group 2: align the general status labels (scannability)

- [x] E-03 In `Term.status_label`/`status`, render the general status words (OK/FAIL/WARN/SKIP/STALE/CURRENT/NOT-INSTALLED/...) at a FIXED WIDTH (pad to the longest label, e.g. `NOT-INSTALLED`) so the message column aligns on a TTY (UX-002). Keep the word + color (color redundant). Do NOT change the machine/`--agent`/`--json` output (those must stay byte-stable); this padding is the human-TTY branch only. Confirm no test that asserts exact `status()` output breaks (update any that pin the unpadded form).
  - Depends on: E-01
  - Expected outcome: colored `aw list-repos` aligns the path column across STALE/CURRENT/NOT-INSTALLED rows; machine output unchanged.
  - Execution state: performed

### Task group 3: uniform non-TTY machine-output flag

- [x] E-04 Standardize the machine-output FLAG NAME (not the format) on read verbs (UX-003). Survey today: `check/find/search/index` (both --json + --agent), `attention`/`doctor`/`backlog check` (only --agent), `status`/`list-repos` (only --json). Decision (maintainer, OQ-02): `--agent` is the ONE universal machine flag every read verb MUST accept; its FORMAT is documented PER VERB - tab-separated Drift-shaped where the data is flat/line-oriented (attention/doctor/sanitizer-style), JSON where the data is nested/typed. Rationale: for flat uniform rows tab output is cheaper in tokens, robust to truncation, and greppable; forcing JSON onto already-clean tab verbs would add a SECOND representation to keep in sync - the exact P8 divergence UX-001 fixes. Add `--agent` to the outliers that lack it: `status`/`list-repos` (which only have `--json`). Keep `--json` working WHERE IT ALREADY EXISTS (check/find/search/index/status/list-repos) as an accepted alias/format - do NOT remove it and do NOT add it to the tab-shaped verbs. Do NOT redefine or reshape any existing `--agent` or `--json` payload; they stay byte-stable. Update each verb's `--help` to state which machine format `--agent` emits for that verb. Do NOT change the DEFAULT (human) output. Net effect: an agent can always reach for `--agent` on any read verb, and the help says what shape to expect.
  - Depends on: none
  - Expected outcome: every machine-facing read verb accepts `--json` and emits valid JSON; `--agent` still works where present; help documents the contract.
  - Execution state: performed

### Task group 4: tests + doc

- [x] E-05 Add `tests/test_term_severity.py` asserting: severity_label bracketed fixed-width alignment (ERROR/WARN/INFO), color-on vs NO_COLOR (word always present, no ANSI when off), and status_label padding (E-03); assert `aw doctor` labels come from Term (no private helpers). Add/extend a machine-flag test asserting each targeted read verb accepts `--agent` and emits its documented machine format (parse tab rows for flat verbs / `json.loads` where nested), and that status/list-repos now accept `--agent` (E-04). Add a short "output conventions" note (TTY concise+colored via Term; non-TTY `--json`/`--agent` machine) to CONTRIBUTING.md or the Term module docstring (UX-005), cross-referencing GUIDING_PRINCIPLES P14. Run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: new/updated tests pass; the output-conventions note exists; full serial suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Severity-label convention is GUIDING_PRINCIPLES P14: bracketed, fixed-width, WORD bold-colored ([ERROR] red / [WARN ] yellow / [INFO ] green), word always present for monochrome/NO_COLOR honesty.
- ALL colored output routes through `agent_workflows/term.py` `Term` (0 hand-rolled ANSI elsewhere) - so one helper change propagates to 195 `status()` call sites.
- `doctor.py:24/29/34` (`tag_error`/`tag_warn`/`tag_info`) ALREADY hand-implements the P14 bracket labels privately; `Term.status_label`/`_STATUS_STYLE` (term.py:146) does NOT - it emits bare variable-width words. That divergence is the core finding.
- Color policy: `should_color` (term.py:56) honors NO_COLOR/FORCE_COLOR/TTY/--no-color; correct and must be preserved.
- Plans lifecycle: `.aw/records/plans/{pending,executed,superseded,not-executed,reusable}`; front-matter Status readiness; IPD born `to-review`. Framework dir + workflow-artifacts are out of assessment scope.

## Findings

| ID | Severity | Remediation Risk | Persona | Evidence | Finding |
|----|----------|------------------|---------|----------|---------|
| UX-001 | High | C:Low U:Low S:Low F:Low Overall:Low | power-user; UI/UX | term.py:146; doctor.py:25/30/35; GUIDING_PRINCIPLES P14 | P14 bracketed labels are hand-rolled in doctor.py but the canonical Term helper (195 sites) emits bare words - duplicate/divergent impl (P8). |
| UX-002 | Medium | Low (usability) | UI/UX; novice | live `aw list-repos` (STALE vs NOT-INSTALLED misalign) | Variable-width bare status words make the message column ragged; hurts TTY scannability. |
| UX-003 | Medium | Low (usability) | power-user; stakeholder | per-verb --help matrix | Non-TTY machine flags inconsistent: check/find/search/index have --json+--agent; attention/doctor/backlog check only --agent; status/list-repos only --json - no uniform agent flag. Resolution (OQ-02): standardize the FLAG NAME `--agent` everywhere, format documented per verb; do not force JSON onto tab-shaped verbs. |
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
- UX-004 (richer empty-state hints) and a broader empty/loading/error-state pass across every verb are OUT OF SCOPE here; per maintainer decision (OQ-01) they are tracked as a SEPARATE release-blocking high-priority backlog item, not expanded into this IPD.

## Scope check

- Over-scope: none - each change targets a found defect; no new features.
- Under-scope: does not touch accessibility (separate lens) or self-documentation/help-text quality (covered by the executed awhelp Set).

## Required tests / validation

`tests/test_term_severity.py` + a machine-flag test (every read verb accepts `--agent`; status/list-repos newly so); full serial suite green; `aw doctor` labels visually unchanged; `aw list-repos` columns aligned under FORCE_COLOR; all pre-existing machine (`--agent`/`--json`) output byte-stable.

## Spec / documentation sync

Add an "output conventions" note (CONTRIBUTING.md or Term docstring) cross-referencing GUIDING_PRINCIPLES P14 (E-05). No spec governs CLI cosmetics.

## Open questions

### OQ-01: Should empty/loading/error-state feedback be standardized across ALL verbs (a broader UX pass), or is the light touch here enough for now?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: OUT OF SCOPE for this IPD. The broad empty/loading/success/error-state UX pass across every verb is tracked as a SEPARATE release-blocking high-priority backlog item `oijafw` (`.aw/records/backlog/open/20260820-awuiux-01-oijafw-...backlog.md`, priority high, `Blocks-Release: next` -> the planned 2.0.0 release record `f33nrj`), filed 2026-08-20 by maintainer directive. This IPD stays the tight labels + machine-flag unification and does NOT expand into the broad pass.

### OQ-02: What machine-output flag should be standardized across read verbs - force `--json` everywhere, or standardize the flag NAME with a per-verb format?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Standardize the FLAG NAME `--agent` as the one universal machine flag on every read verb; its FORMAT is documented per verb (tab-separated for flat/line-oriented data, JSON where nested). Do NOT force `--json` onto tab-shaped verbs (attention/doctor/backlog check), which would re-introduce a second representation to keep in sync (the P8 divergence UX-001 fixes). Rationale: for flat uniform rows tab output is cheaper in tokens, robust to truncation, and greppable; JSON's self-describing/typed advantage applies to nested data. E-04/V-04 rewritten to this decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `Term(color=True).severity_label("error"/"warn"/"info")` returns bracketed labels with the WORD bold-colored (red196/yellow226/green46) and brackets uncolored, padded so ERROR/WARN/INFO brackets align; `Term(color=False)` returns plain `[ERROR]`/`[WARN ]`/`[INFO ]` with no ANSI. Shown by test_term_severity.
  - Observed evidence: `Term(color=True).severity_label("error")` returns `[\x1b[1;38;5;196mERROR\x1b[0m]`, `severity_label("warn")` returns `[\x1b[1;38;5;226mWARN \x1b[0m]`, `severity_label("info")` returns `[\x1b[1;38;5;46mINFO \x1b[0m]`; `Term(color=False)` returns plain `[ERROR]`, `[WARN ]`, `[INFO ]`. Validated by `test_severity_label_color_on` and `test_severity_label_color_off` in `tests/test_term_severity.py`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `doctor.py` has no private `tag_error`/`tag_warn`/`tag_info` bracket helpers (`grep -n 'def tag_error\|def tag_warn\|def tag_info' agent_workflows/doctor.py` empty); `aw doctor` still prints identical `[INFO ]`/`[WARN ]`/`[ERROR]` labels, now sourced from Term.
  - Observed evidence: `grep -n 'def tag_error\|def tag_warn\|def tag_info' agent_workflows/doctor.py` returned empty (exit code 1); `doctor.py` calls `term.severity_label("error"/"warn"/"info")`; verified by `DoctorSeveritySourceTests` in `tests/test_term_severity.py`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: under FORCE_COLOR, `aw list-repos` aligns the path column across STALE/CURRENT/NOT-INSTALLED rows (fixed-width labels); `--agent`/`--json`/machine output byte-unchanged (diff before/after empty).
  - Observed evidence: `Term.status_label` pads all status words to 13 characters (`_STATUS_WIDTH`), ensuring the message/path column starts at column 15 across STALE/CURRENT/NOT-INSTALLED rows under both FORCE_COLOR and monochrome TTY modes; verified by `TermStatusLabelPaddingTests`. INDEPENDENT byte-stability check (opencode, diff vs pre-agy baseline at 0476654): the 4 pre-existing tab `--agent` payloads (check backlog / find plans / attention / doctor) diff EMPTY; `status --json` / `list-repos --json` diff only in the embedded `packaged_version` git-hash + `ahead` count (dev728+g0476654 -> dev729+gdd1b964), which move because agy added a commit - the JSON structure/payload is otherwise byte-identical. No machine-payload regression.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: every targeted read verb (check/find/search/index/attention/doctor/status/list-repos/backlog check) accepts `--agent` (the newly added ones being status/list-repos) and emits its documented machine format (tab-separated for flat verbs, JSON where nested); the pre-existing `--agent` and `--json` payloads are byte-unchanged (diff before/after empty on every verb that already had them); `--json` still works where it already existed and was NOT added to the tab-shaped verbs; each verb's `--help` states which machine format `--agent` emits.
  - Observed evidence: INDEPENDENT opencode check - `--agent` accepted on check/find/search/index/attention/doctor/status/list-repos/backlog check (the three nonzero exits are legitimate content reasons, NOT flag rejection: `check backlog` exit 1 = findings present, `search plans` exit 2 = needs a positional pattern, `doctor` exit 1 = untracked-file drift; each still emits its tab rows); `status`/`list-repos` (newly added) accept `--agent` and emit machine JSON identical to `--json`; `--json` correctly REJECTED on attention/doctor/backlog check and PRESERVED on find/status/list-repos. Verified by `MachineOutputFlagsTests` in `tests/test_term_severity.py`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_term_severity.py -p no:xdist -q` green; the output-conventions note exists (CONTRIBUTING.md or Term docstring, cross-refs P14); full serial suite tail pasted.
  - Observed evidence: INDEPENDENT opencode run - `python3 -m pytest tests/test_term_severity.py -p no:xdist -q` => 16 passed; output-conventions note added to `CONTRIBUTING.md` (cross-refs GUIDING_PRINCIPLES.md P14); FULL serial suite `python3 -m pytest -p no:xdist` => `1243 passed, 1 skipped in 242.18s (0:04:02)`. Also `aw sanitize --agent` rc=0 (no tracked-file leaks) and `aw attention --check` = valid. Note: the E-03 padding change correctly updated the pinned assertion in `tests/test_install_wizard.py` ("OK  Policy validated." -> "OK             Policy validated.").
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST be human-approved (Status: approved) before execution; it is not auto-run. Execution contract: commit only files changed by the plan, path-scoped, never push; run the full serial suite and paste the ACTUAL runner output as V evidence; keep `--agent`/`--json` machine payloads byte-stable (human-TTY changes only); on completion lint --phase pre-transition while approved, then flip to executed + executed history + git mv to executed/ + post-transition lint. Do not mark executed until every V item is verified with concrete evidence.
