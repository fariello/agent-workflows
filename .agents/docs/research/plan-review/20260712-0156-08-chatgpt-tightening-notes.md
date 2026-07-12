# Plan Review Tightening and Modularization Notes

## Result

The tightened single-file runbook is 417 lines, down from about 780 lines.
It is about 47 percent shorter while preserving the substantive corrections.

The modular package adds a durable checklist and phase-local instruction files.
This is the recommended form for repeated execution by long-context or
lower-cost coding agents.

## Why modularization helps

Modularization reduces directive drift only when it changes what is active in
the model's working context.

The useful pattern is:

1. Keep a small non-negotiable memory kernel in the orchestrator.
2. Load one active step at a time.
3. Read the active step and exit gate last.
4. Persist state and evidence in a checklist outside conversational memory.
5. Do not load all modules up front.
6. Do not duplicate global rules across modules.

This improves reliability through:

- **Recency:** active instructions are near the end of context.
- **Reduced competition:** inactive rubric and reporting detail do not compete
  with the current step.
- **State externalization:** scope, findings, questions, and commits survive
  context compaction or agent handoff.
- **Phase gates:** the agent cannot advance without explicit checklist evidence.
- **Recovery:** a resumed agent can reconstruct status from repository files.

## Why a checklist adds value

A checklist is more useful than repeated prose when it is a state record, not
a ceremonial list.

The provided `review-state-template.md` records:

- Scope ledger.
- Controlling instructions and project contract.
- Pre-review snapshot result.
- Evidence readiness.
- Finding and Remediation Risk status.
- Open-question status.
- Plan edits and invariant coverage.
- Final status and commit result.
- Verdict and readiness.
- Final-output guard.

Each checked item requires an evidence or result field. The checklist therefore
acts as a compact execution ledger and compaction-recovery point.

## What modularization does not solve

Splitting files can make execution worse when:

- The orchestrator is too vague.
- Global non-negotiable rules exist only in an early file.
- Every module is loaded at once.
- Rules are copied into several files and drift.
- Steps are split too finely.
- The checklist rewards checking boxes without evidence.
- The final report template is not loaded immediately before reporting.

The package avoids these problems with one orchestrator, three steps, one
rubric, one report template, and one state template.

## Recommended use

Use the modular package as the canonical installed workflow.

Keep the tightened single-file version as a portable fallback for environments
that cannot reliably load sibling files.

Do not hand-maintain both independently. Generate the fallback from the modular
source, or run a semantic parity test that checks for the required invariants.

## Preserved substantive improvements

The tightened and modular forms both preserve:

- Verdict separate from GO/NO-GO readiness.
- `REVIEWED - OPEN QUESTIONS`.
- Defined Low, Medium, Medium-High, and High Remediation Risk.
- Overall risk equals the highest applicable axis.
- Step 0 review-scope ledger.
- Consistent `NOT REVIEWED` label.
- Evidence-first question resolution.
- One to three related interactive questions using the fixed six-part format.
- Recording answers into the plan and re-checking affected areas.
- Delayed reply is not non-interactive.
- `Status: reviewed` does not mean approved, GO, or executed.
- At most two local commits.
- Dirty-tree and commit-failure safety.
- Never push.
- Evidence field and commit result in the final report.
- Final reviewed/not-reviewed enumeration as literal last output.
- Fix by default.
- Severity never decides.
- Effort, time, cost, and tokens never justify deferral.
- Planning-documents-only boundary.
- Tool-agnostic and project-agnostic behavior.
- Relative release-review sibling references with graceful degradation.
- Eight personas with security as a cross-cutting lens.
