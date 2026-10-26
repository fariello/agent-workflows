# Plan Review (pre-execution plan / IPD reviewer)
Treat this file as the controlling instruction for reviewing a proposed plan
before implementation, then improving that plan in place.

This portable single-file checklist is SERIAL BY DESIGN: it does not auto-fan-out into parallel audit
lanes (a lone portable file spawning subagents is awkward and not universally available). For a
multi-plan batch that should review plans in parallel, use `../plan-review-long/plan-review-long.md`,
which auto-engages the read-only audit-lane convention (`../release-review/00-run-protocol.md`) when the
scope ledger has 2 or more eligible plans. The two variants are otherwise kept in deliberate parity.

## Step 0: Scope and pre-pass

### 0.1 Build the review-scope ledger
The ledger contains ONLY the plans explicitly named in the invocation, plus any
that the project's own documented eligibility rules add. Do NOT enumerate other
plans in the repository (e.g. everything in `pending/` or `executed/`) to build
the ledger. A "candidate" is a ledger entry: an explicitly named target, or a
plan a documented eligibility rule adds. A plan that was never a candidate is an
"incidental file" and MUST NOT appear in the ledger or the final report.

Classify each candidate as:
- `ELIGIBLE` - review it.
- `NOT REVIEWED` - a candidate skipped, with the exact reason (missing,
  unreadable, malformed beyond review, not a planning document, or wrong status
  per project rules). NOT REVIEWED NEVER lists a plan that was never a candidate.
  If the ledger is exactly the requested target(s) and none were skipped, the
  final NOT REVIEWED section is `(none)`.

Use project eligibility and status rules when present. Otherwise review an
explicitly requested plan unless it is missing, unreadable, malformed beyond
review, or not a planning document.

A file referenced only as evidence is not in scope unless explicitly added.

The final enumeration MUST contain every ledger CANDIDATE and no incidental file.

### 0.3 Discover the plan contract and implementation context
Determine:
- Plan location, structure, front matter, status lifecycle, approval rules,
  traceability, workflow history, and commit rules.
- Project type, languages, frameworks, production runtime and data store,
  deployment model, integrations, security model, and test stack.
- Domain invariants from specifications, principles, ADRs, accepted plans,
  code, tests, constraints, and authoritative conversation context.

Apply the rubric to the real production target.

If the plan changes behavior, policy, workflow, API, authorization, state, or
domain rules, require specification and documentation synchronization.

If no project principles exist, use these fallbacks and record that choice:
- Intuitive and self-documenting.
- General-case and configurable.
- KISS.
- Honest documentation.

### Pre-review commit
Before editing:
1. Inspect repository status.
2. Isolate the eligible plan files.
3. If any target plan is untracked or modified, commit those plan files
   verbatim as:

   `plan: pre-review snapshot of <scope>`

4. If all target plans are committed and unchanged, skip the snapshot.

Never stage unrelated files. Never amend, reset, rebase, discard user changes,
or push.

If Git is unavailable or a commit fails, continue only when safe and record the
reason. Do not bypass hooks or safety controls unless project rules permit it.

### Structural preflight (before semantic review)
For each eligible plan that is an agent-executable IPD, run the deterministic structural linter as
a GATE before you spend semantic effort:

    aw ipd lint --phase author --agent <plan-file>

For an orchestrator, also check coverage:

    aw ipd coverage <id6>

Then, after all revision edits are applied (Step 2/3), re-run at the finalize checkpoint:

    aw ipd lint --phase review-finalize --agent <plan-file>

Only a `conforming` disposition proceeds. Exit `1` (a conformance error) is a distinct STRUCTURAL
finding that MUST be repaired before a passing verdict; exit `2` (the linter could not run) is a
hard stop, not a skip. INVOKE the linter; do not paraphrase or hand-simulate its checks. The linter
proves STRUCTURE and STATE only (heading order, `E-*`/`V-*` bijection, state legality, metadata,
and coarse count thresholds); it establishes nothing semantic (coverage, correctness, evidence
sufficiency, truthful blocking-classification, or conceptual density per E-item), so the semantic
review below remains fully required and separate. A passing count-based size lint does NOT
clear right-sizing; conceptual density must be evaluated in semantic review.

## Review checklist

For each eligible plan, execute the following steps in order. When recording findings, read and apply `steps/_findings.md`.

1. Read and apply `steps/_kernel.md`.
2. Read and apply `steps/p-proofread.md`.
3. If the plan is an Order-00 orchestrator, skip check T (orchestrators are not rated by T, per spec `k3yx72` Section 5.1). Otherwise, read and apply `steps/t-tier.md` to rate the plan as `simple`, `standard`, or `complex`.
4. Run the checks for the assigned tier, reading and applying `steps/_findings.md` with each check:
   - **`simple` tier:**
     - Read and apply `steps/q-quick-risk.md`.
     - When tier question 2 is "yes" (touches code guarding private data, commits, worktree isolation, or the sandbox), read and apply the short form of `steps/r3-security.md`.
   - **`standard` tier:**
     - Read and apply `steps/r1-references.md`.
     - Read and apply `steps/r2-executability.md`.
     - Read and apply `steps/r3-security.md` (full form).
     - Read and apply `steps/r4-engineering.md`.
   - **`complex` tier:**
     - Read and apply `steps/r1-references.md`.
     - Read and apply `steps/r2-executability.md`.
     - Read and apply `steps/r3-security.md` (full form).
     - Read and apply `steps/r4-engineering.md`.
     - Read and apply `steps/r5-personas.md`.
     - Read and apply `steps/r6-decomposition.md`.
     - For plans in a Set, read and apply `steps/r7-cross-plan.md`.
   - **`orchestrator`:**
     - Read and apply `steps/r1-references.md`.
     - Read and apply `steps/r2-executability.md` (child table, coverage repair loop `IPD-S408`, row check `IPD-S407`).
     - Read and apply `steps/r7-cross-plan.md` across the entire Set.
5. Read and apply `steps/s5-questions.md` to resolve open questions and escalate unfixed gating findings.
6. Read and apply `steps/s6-rereview.md` to decide if an additional pass is needed (looping at most twice).
7. Read and apply `steps/s7-finalize.md` to record the readiness, workflow history entry, commit, and final report.
