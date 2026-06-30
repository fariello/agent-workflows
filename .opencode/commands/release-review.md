---
description: Run the full release readiness repository review
agent: build
---

Read and execute @release-review/README.md.

Treat that file as the controlling instruction for this repository review. Complete the full runbook (Sections 1 through 8), reviewing through all eight expert personas (QA/QC, testing/regression, UI/UX, architect, software engineer, power user, novice, stakeholder). On this run: reconcile any `TODO.md`/backlog against the release, honor the repository's guiding principles, hold the self-documenting / learn-as-you-go bar, treat memory/resource and live-interaction-surface correctness as first-class, and write a per-phase report for each section. Create the required run artifacts, use TodoWrite if available, use controlled parallel read-only audit lanes when useful, commit between phases, do not push unless explicitly permitted, perform final validation, and produce the final table-first report.

Do not perform Section 9 (release execution: push/tag/publish/deploy) unless the final recommendation is GO or CONDITIONAL GO and the user explicitly approves performing the release.
