# AGENTS

<!-- AGENT-WORKFLOWS:BEGIN -->
## Agent workflows

This repository includes reusable agent workflows under `.agents/workflows/`. They are invoked on demand and are NOT always-loaded context. See `.agents/workflows/index.md` for the list and how to run each (native `/commands` in OpenCode/Claude Code, or "read and execute <body path>" in any other agent).
<!-- AGENT-WORKFLOWS:END -->

<!-- AGENT-PLANS:BEGIN -->
## Agent plans

This repository follows a structured Implementation Plan Document (IPD) lifecycle:
1. **Pending**: New or proposed plans are placed under `.agents/plans/pending/` named `YYYYMMDD-HHMM-NN-<slug>.md` (UTC date and time; `NN` is a two-digit per-minute sequence, with `00` reserved for an orchestrator plan and `01+` for ordinary/child plans; `<slug>` is lowercase kebab-case).
2. **Review/Approval**: Plans are reviewed (optionally using `/plan-review`), aligned with human feedback, and must receive explicit human approval before execution.
3. **Reusable Runs**: Recurring plans or rollouts that are executed repeatedly stay under `.agents/plans/reusable/`.
4. **Execution**: Approved one-off plans are executed, and once implemented, verified, and tested, the IPD is moved to the terminal directory `.agents/plans/executed/`.
5. **Retirement (superseded / not-executed)**: A plan that is never run is NOT filed under `executed/` (that would falsely claim implementation). Instead, prepend a `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` header and `git mv` it to `.agents/plans/superseded/` (replaced by a better/subsequent plan) or `.agents/plans/not-executed/` (deliberately decided against, no replacement). Never silently delete a plan; retiring preserves the record and the reason.
<!-- AGENT-PLANS:END -->
