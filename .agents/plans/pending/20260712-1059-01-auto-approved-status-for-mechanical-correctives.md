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
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): decided interactively with the
  maintainer while designing /verify-execution. Complete proposal; born to-review.

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
   an automated check rather than a human; used for small mechanical correctives (see D64)".
4. **Wire `/verify-execution` (IPD 20260712-1031-01) to emit `auto-approved` under STRICT criteria.**
   The corrective IPD is born `auto-approved` ONLY when ALL hold:
   - it is fully specified ("do exactly X"), with no new design decision to make;
   - zero open questions;
   - small blast radius (a bounded diff / few files - name a concrete cap, e.g. <= ~3 files);
   - it CORRECTS already-reviewed work (completion/fix), not new scope.
   Otherwise it is born `to-review`. Err toward `to-review` when unsure. Record the choice in a
   Workflow-history line: `auto-approved by /verify-execution (criteria: <which>)`. Add an `Approval:`
   line `auto-approved by /verify-execution <date>; not human-reviewed`.
5. **Executor + guardrails.** Document that an executor may run an `auto-approved` IPD without human
   review, BUT (a) must still run the plan's stated validation and only set `executed` if it actually
   passes (the 1043-01 rule), and (b) must never SELF-promote a plan it authored from a lower state to
   `auto-approved` outside the /verify-execution criteria - `auto-approved` is set by the CHECKING
   agent for a corrective, not by an executor to fast-track its own work.
6. **`aw plans` board + docs.** Board displays `auto-approved` in its lifecycle slot (after
   `approved`); README/relevant docs mention it. DECISIONS entry (D64) records the token, its meaning,
   the strict emit criteria, the executor rule, and that it deliberately does NOT count as human
   approval.

## Deferred / out of scope

- Applying `auto-approved` to any workflow other than /verify-execution for now (e.g. letting
  /assess auto-approve). Keep it to machine-verified correctives; revisit if a second use appears.
- A hard machine gate enforcing the "strict criteria" (advisory-first per D52; the criteria are prose
  the checking agent applies, plus the recorded rationale for audit).

## Open questions (v1 leans for review)

1. Blast-radius cap for auto-approval: a concrete number (e.g. <= 3 files AND no new function/public
   API) vs. a judgment call. (Lean: name a soft cap of ~3 files + "no new design decision", and
   downshift to to-review above it - concrete enough to be consistent, with judgment for edge cases.)
2. Token name: `auto-approved` vs `ready` vs `machine-approved`. (Lean: `auto-approved` - reads as a
   sibling of approved, clearly not human.)
3. Should `auto-approved` also be allowed for a human to set manually (a fast-track), or ONLY by an
   automated checker? (Lean: only by an automated checker; a human who wants fast-track just uses
   `approved`. Keeps the token's meaning precise.)

## Approval and execution gate

`to-review`. Next: `/plan-review` (resolve OQs interactively), human approve, execute changes 1-6,
validate (suite green incl. the drift-guard; `aw plans` shows the token), commit (never push),
`git mv` to executed/. Dependency: IPD 20260712-1031-01 (/verify-execution) consumes this token, so
land this first or together. Not auto-executed.
