# IPD: Add an `auto-approved` readiness status for small mechanical corrective IPDs

- Date: 2026-07-12
- Concern: plan lifecycle / velocity without eroding honesty. Corrective IPDs emitted by
  `/verify-execution` (and similar "you forgot to do X, do exactly this" fixes) are usually tight,
  fully-specified, already-cross-checked, and low-risk. Forcing them through human `to-review` ->
  `reviewed` -> `approved` is low-value ceremony. But reusing `approved` for a machine judgment would
  falsely imply human sign-off (violating the honest-record ethos and the D52/P10 human-approval
  gate). This IPD adds a DISTINCT, honest status that means "an agent judged this a safe mechanical
  corrective, ready to run, NOT human-approved".
- Scope: extend the D52 readiness vocabulary with `auto-approved`; update the shared parser
  (`agent_workflows/plans.py`), the drift-guard test, the IPD template, the `aw plans` board ordering,
  DECISIONS, and wire `/verify-execution` (IPD 20260712-1031-01) to emit it under strict criteria.
- Status: executed
- Approval: approved by maintainer 2026-07-12. Executed 2026-07-12 (its_direct/pt3-claude-opus-4.8-1m-us);
  full suite green (207).
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): decided interactively with the
  maintainer while designing /verify-execution. Complete proposal; born to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  Verified against source: PRE_TERMINAL (plans.py:22) is the single vocab source, drift-guard imports
  RECOGNIZED/DIR_TERMINAL/LEGACY_MAP from it, and auto-approved is pre-terminal so the terminal-vs-dir
  rule is unaffected. All 3 OQs resolved interactively (complexity-not-file-count bar; name
  auto-approved; checker-only). Fixed the DECISIONS number (D65; D64 already taken). Status -> reviewed.
- 2026-07-12 approved + executed (its_direct/pt3-claude-opus-4.8-1m-us): added auto-approved to
  plans.py PRE_TERMINAL (+ board order idx 4); drift-guard test test_auto_approved_is_recognized_and_
  pre_terminal; IPD template legend + D52 pointer; DECISIONS D65; wired the complexity-based emit
  criteria into the /verify-execution IPD (1031-01). Full suite green (207). Status -> executed.

## Decision taken (maintainer, 2026-07-12)

Introduce a new readiness token `auto-approved`, a SIBLING of `approved` at the "ready to execute"
tier, meaning: a checking agent (e.g. /verify-execution) judged this IPD a small, mechanical,
fully-specified corrective that is safe to run WITHOUT human review, and it was NOT human-approved.
An executor MAY run an `auto-approved` IPD without waiting for a human. Everything non-trivial still
goes through human `approved`.

## Project conventions discovered (Step 0, VERIFIED against source)

- Readiness vocabulary is single-sourced in `agent_workflows/plans.py`:
  `PRE_TERMINAL = ("draft","to-review","reviewed","approved")` (:22), `RECOGNIZED` (:25), and the
  board ordering `_READINESS_ORDER` (:50). The drift-guard `tests/test_plan_status.py` imports
  `RECOGNIZED`/`DIR_TERMINAL`/`LEGACY_MAP` from there, so adding the token in ONE place propagates.
- The vocabulary legend also lives in `.agents/workflows/assess/templates/ipd.md` (the comment block)
  and DECISIONS D52. Both must gain `auto-approved`.
- `auto-approved` is a PRE-TERMINAL state (the file still lives in `.agents/plans/pending/` until it
  executes and moves to `executed/`), exactly like `approved`. It is NOT a terminal/dir-mirrored
  status, so the drift-guard's terminal-vs-dir rule is unaffected.
- The validate-before-executed rule (IPD 20260712-1043-01, in flight) still binds: `auto-approved`
  never lets an executor skip actually running the plan's stated validation before marking `executed`.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Vocabulary (`plans.py`).** Add `auto-approved` to `PRE_TERMINAL` (adjacent to `approved`) so it
   is `RECOGNIZED` and gets a board-ordering slot. Place it right after `approved` in `_READINESS_ORDER`.
2. **Drift-guard test.** It picks up the new token automatically via the shared `RECOGNIZED` import;
   add an explicit assertion that `auto-approved` is recognized and is treated as pre-terminal (a plan
   with `Status: auto-approved` must live in `pending/`, not a terminal dir).
3. **IPD template + D52 legend.** Add `auto-approved` to the vocabulary comment in
   `templates/ipd.md` and to DECISIONS D52's enumerated set, defined as: "ready to execute, cleared by
   an automated check rather than a human; used for low-complexity mechanical correctives (see D65)".
4. **Wire `/verify-execution` (IPD 20260712-1031-01) to emit `auto-approved` under criteria judged by
   COMPLEXITY/RISK, not file count (OQ1 resolved).** The corrective IPD is born `auto-approved` when:
   - it is fully specified ("do exactly X"), with no new design decision to make;
   - zero open questions;
   - it CORRECTS already-reviewed work (completion/fix), not new scope; and
   - the change is LOW-COMPLEXITY / low-risk by judgment - the axis is complexity, NOT number of
     files. Illustration: changing `foo`->`bar` across 25 Markdown files is mechanical and fine to
     auto-approve; "refactor biz.js" where biz.js is the security core of an API is NOT, even though
     it is one file. Apply sound judgment and ERR TOWARD `to-review` only when genuinely UNCERTAIN
     about complexity. Do not be super-cautious for its own sake: this is a corrective to an
     already-hyper-cautious (reviewed) IPD, and most agentic coding ships with no IPD or review at
     all, so a proportionate bar is appropriate.
   Otherwise it is born `to-review`. Record the choice in a
   Workflow-history line: `auto-approved by /verify-execution (criteria: <which>)`. Add an `Approval:`
   line `auto-approved by /verify-execution <date>; not human-reviewed`.
5. **Executor + guardrails.** Document that an executor may run an `auto-approved` IPD without human
   review, BUT (a) must still run the plan's stated validation and only set `executed` if it actually
   passes (the 1043-01 rule), and (b) must never SELF-promote a plan it authored from a lower state to
   `auto-approved` outside the /verify-execution criteria - `auto-approved` is set by the CHECKING
   agent for a corrective, not by an executor to fast-track its own work.
6. **`aw plans` board + docs.** Board displays `auto-approved` in its lifecycle slot (after
   `approved`); README/relevant docs mention it. DECISIONS entry (D65 - note D64 already exists)
   records the token, its meaning, the complexity-based emit criteria, the executor rule, and that it
   deliberately does NOT count as human approval.

## Deferred / out of scope

- Applying `auto-approved` to any workflow other than /verify-execution for now (e.g. letting
  /assess auto-approve). Keep it to machine-verified correctives; revisit if a second use appears.
- A hard machine gate enforcing the "strict criteria" (advisory-first per D52; the criteria are prose
  the checking agent applies, plus the recorded rationale for audit).

## Open questions (RESOLVED with maintainer 2026-07-12)

1. Auto-approval bar: RESOLVED - judged by COMPLEXITY/RISK, NOT file count. A large-but-mechanical
   change (e.g. `foo`->`bar` across 25 files) can auto-approve; a small-but-risky one (refactoring an
   API's security core) cannot. Sound judgment, err toward `to-review` only on genuine complexity
   uncertainty; do not be super-cautious for its own sake (we are already correcting a hyper-cautious
   reviewed IPD). See change #4.
2. Token name: RESOLVED - `auto-approved` (a clear sibling of `approved`, obviously not human).
3. Who may set it: RESOLVED - ONLY an automated checker (e.g. /verify-execution). A human wanting a
   fast-track just uses `approved`; keeps the token's meaning precise.

## Approval and execution gate

`to-review`. Next: `/plan-review` (resolve OQs interactively), human approve, execute changes 1-6,
validate (suite green incl. the drift-guard; `aw plans` shows the token), commit (never push),
`git mv` to executed/. Dependency: IPD 20260712-1031-01 (/verify-execution) consumes this token, so
land this first or together. Not auto-executed.
