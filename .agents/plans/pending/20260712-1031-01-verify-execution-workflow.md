# IPD: New /verify-execution workflow - cross-check that an executed plan was actually done

- Date: 2026-07-12
- Concern: new capability. There is no reusable way to verify that an executed IPD was actually
  implemented as written - which matters especially when a DIFFERENT agent (or a past session)
  executed it. This session did that cross-check by hand for Gemini's `0954-01` execution (found the
  engine sound but the test suite left red) and emitted a corrective IPD manually. This workflow
  generalizes that proven pattern.
- Scope: a new workflow `.agents/workflows/verify-execution/` (body + README), a manifest row in
  `index.md` (shims regenerate), reuse of the existing `/verify` workflow for running the repo's real
  checks, tests for any mechanical bits, docs + DECISIONS. Distinct from `/plan-review` (pre-execution
  planning review) and `/release-review` (broad ship review).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): drafted after hand-executing the
  cross-check on Gemini's 0954-01 work; design decisions taken with the maintainer. Complete
  proposal; born to-review.

## Design decisions taken (maintainer, 2026-07-12)

1. Name: `/verify-execution`. Sits beside `/verify` (runs checks) and `/plan-review` (pre-execution).
2. Input: an EXECUTED plan/IPD path (+ optional commit or range). If no range is given, discover the
   execution commit(s) from git log and the plan's `## Workflow history`.
3. PURE VERIFIER: it NEVER fixes code/tests in place. For any gap it EMITS a corrective IPD into
   `.agents/plans/pending/`. This keeps the checker non-destructive and safe when another agent owns
   the code (no collision).
4. Verdict contract: `MATCHES` / `DIVERGES` / `INCOMPLETE`, plus a final GO/NO-GO on the real
   question - "should this plan be considered truly executed, or bounced back?".
5. Agent-agnostic: works whether the executor was another agent (e.g. Antigravity/Gemini), a prior
   session, or a human.

## What the workflow does (body outline)

1. **Load the executed plan** and extract its REQUIRED changes: proposed-changes list, required
   tests/validation, spec/doc-sync obligations, and any plan-review findings it agreed to fix.
2. **Discover the execution evidence:** the commit(s) that executed it (from the arg, else git log /
   the plan's Workflow history) and the resulting diff. Read the ACTUAL diff, do not trust the commit
   message.
3. **Check each required change was actually done** against the diff (re-open the evidence at
   `file:line`, the same discipline as plan-review). Classify each as done / partial / missing /
   diverged (done differently than the plan said) / over-scope (done but not in the plan).
4. **Re-run the repo's real validation** by reusing `/verify` (discover and run the project's
   test/lint/build/type-check commands; capture real exit codes). A RED suite that the execution
   introduced or left is a finding. Note any pre-existing red baseline separately so it is not
   misattributed.
5. **Verdict + emit corrective IPD.** State `MATCHES`/`DIVERGES`/`INCOMPLETE` and a GO/NO-GO on
   "truly executed?". For every gap, write ONE corrective IPD (named
   `YYYYMMDD-HHMM-NN-fix-<original-slug>-<short>.md`) describing exactly what was missed/diverged and
   what must be done, cross-referencing the original plan and the execution commit(s). Never fix in
   place. If MATCHES with a green suite and no gaps, emit NO IPD and say so.
   - **Status of the corrective IPD (D65):** born `auto-approved` (ready to execute without human
     review) when the correction is fully specified, has zero open questions, corrects
     already-reviewed work, and is LOW-COMPLEXITY/low-risk - judged by COMPLEXITY, not file count (a
     large mechanical `foo`->`bar` sweep can auto-approve; a small risky refactor of critical logic
     cannot). Add an `Approval:` line `auto-approved by /verify-execution <date>; not human-reviewed`
     and a Workflow-history line recording the rationale. Otherwise born `to-review`. Err toward
     `to-review` ONLY on genuine complexity uncertainty. `auto-approved` is set by this CHECKER, never
     by an executor fast-tracking its own work; and an `auto-approved` plan still must pass its stated
     validation before being marked `executed` (D64).
6. **Report** in a fixed format ending with the verdict + GO/NO-GO as the last output (mirror the
   plan-review report discipline).

## Boundary / safety

- Read-only on code: inspects the plan, git history, and diffs; runs the repo's OWN validation via
  /verify (which has its own denylist for network/deploy/publish). Writes ONLY a corrective IPD (and
  its own run record). Never pushes. Never edits the executed code/tests (that is the corrective IPD's
  job, executed separately, by whichever agent).
- Honest about attribution: distinguishes gaps INTRODUCED by this execution from pre-existing repo
  state (e.g. a suite already red before the execution).
- **Runs safely IN PARALLEL with the executing agent (concurrency rule).** This workflow is often
  run WHILE another agent is still working in the same repo (that is the whole point: cross-checking
  another agent's work). Therefore it MUST commit ONLY the file(s) IT creates - normally a single
  corrective IPD (plus its own run record). Commit path-scoped (`git commit -- <that-file>`), NEVER a
  bare `git commit` or `git add -A`/`git commit -a`, because the other agent may have unrelated files
  staged in the index and a bare commit would sweep THEIR in-flight work into yours. Do not stage,
  amend, revert, `git mv`, or reset any file this workflow did not itself create. Do not rewrite
  history while another agent may be active. If the working tree/index shows another agent's
  in-progress changes, that is expected - leave them entirely alone and commit only your IPD by exact
  path. (Learned from a real collision: a bare commit here swept a concurrently-running agent's staged
  renames into the wrong commit.)

## Proposed changes (ordered, validatable)

1. **Author `.agents/workflows/verify-execution/verify-execution.md`** implementing the outline above,
   in the house LLM-reliability style (MUST/SHOULD, ordered steps, a fixed report format ending in the
   verdict + GO/NO-GO). Reference `/verify` for running checks and `plan-review/fix-decision-policy.md`
   for how it rates the gaps it reports (it reports, it does not fix). Tool-agnostic; graceful when
   git or /verify siblings are absent.
2. **`.agents/workflows/verify-execution/README.md`** (Category-2 authored; every top-level workflow
   dir needs a README per D49 and the dir-readmes test).
3. **Register in `index.md`:** `verify-execution | .agents/workflows/verify-execution/verify-execution.md
   | - | <desc>`; regenerate shims.
4. **Docs + DECISIONS:** add `/verify-execution` to the README command table and ARCHITECTURE; a
   DECISIONS entry recording the workflow, the pure-verifier/emit-a-corrective-IPD contract, the
   MATCHES/DIVERGES/INCOMPLETE + GO/NO-GO verdict, and its distinction from /plan-review and
   /release-review.
5. **Tests:** prose workflow (no unit test for instruction prose, per repo policy); the manifest/shim
   wiring must keep the suite + dir-readmes test green. If any mechanical helper is added (e.g. a
   commit-range discovery snippet), unit-test it.

## Open questions (v1 leans for review)

1. Should there also be a modular `/verify-execution-long` (like plan-review has), or single-file
   only for now? (Lean: single-file only; revisit if the body grows or the plan-review A/B favors
   modular.)
2. Corrective-IPD naming: `YYYYMMDD-HHMM-NN-fix-<original-slug>-<short>.md` vs a plain new slug.
   (Lean: reference the original slug so the pairing is obvious.)
3. Does it also consume the ORIGINAL plan-review record (the findings the plan agreed to fix), to
   verify those specific fixes landed? (Lean: yes - agreed plan-review findings are part of "what was
   required".)
4. Should MATCHES-with-green auto-nothing, or always leave a short run record? (Lean: always write a
   brief run record for provenance, even on a clean MATCHES; emit an IPD only when there are gaps.)

## Approval and execution gate

`to-review`. Next: `/plan-review` (resolve OQs interactively), human approve, execute changes 1-5,
validate (suite + dir-readmes green, shims regenerated, a dogfood run against a real executed plan),
commit (never push), `git mv` to executed/. Not auto-executed.
