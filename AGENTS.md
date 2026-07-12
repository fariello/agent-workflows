# AGENTS

<!-- AGENT-WORKFLOWS:BEGIN -->
## Agent workflows

This repository includes reusable agent workflows under `.agents/workflows/`. They are invoked on demand and are NOT always-loaded context. See `.agents/workflows/index.md` for the list and how to run each (native `/commands` in OpenCode/Claude Code, or "read and execute <body path>" in any other agent).

### Guidelines for Antigravity & Other Agents
When requested to run one of these workflows (e.g. "run release-review", "assess <concern>", "run setup-repo", "run scaffold"):
1. Locate the workflow's entry file under `.agents/workflows/` (referenced in `.agents/workflows/index.md`).
2. Read and execute the instructions defined in that workflow file step-by-step.

### Writing prompts for another AI (research/handoff prompts)
When asked to write a prompt to give to another AI (e.g. a research prompt for an LLM with web search), the prompt you produce MUST be upload-ready:
1. It contains ONLY the prompt itself, addressed to that AI. Put NO instructions for the user inside it (no "copy this", no "paste below the line").
2. It is self-contained, so the user can select-all-and-copy it, or upload it and say "read and execute the attached prompt", with nothing to edit.
3. It instructs the target AI to return its answer as a DOWNLOADABLE markdown (`.md`) file, so the result can be handed back for consumption.
<!-- AGENT-WORKFLOWS:END -->

<!-- AGENT-PLANS:BEGIN -->
## Agent plans

This repository follows a structured Implementation Plan Document (IPD) lifecycle:
1. **Pending**: New or proposed plans are placed under `.agents/plans/pending/` named `YYYYMMDD-HHMM-NN-<slug>.md` (the creating machine's local date and time; `NN` is a two-digit per-minute sequence, with `00` reserved for an orchestrator plan and `01+` for ordinary/child plans; `<slug>` is lowercase kebab-case).
2. **Review/Approval**: Plans carry a front-matter `Status:` recording READINESS within the lifecycle (directories carry disposition; `Status:` carries readiness): `draft` (a stub; not ready) -> `to-review` (complete enough to critique; the default a completed IPD is born with) -> `reviewed` (`/plan-review` done, revisions applied) -> `approved` (explicit human sign-off; ready to execute). Then a terminal `Status:` mirrors the directory (`executed`/`superseded`/`not-executed`; `reusable` is standing). Each plan also keeps an appended `## Workflow history` recording which workflows touched it. The plan-mutating workflows commit at their steps and NEVER push, so the git history shows a plan moving through the pipeline. Explicit human approval is still required before execution.
3. **Reusable Runs**: Recurring plans or rollouts that are executed repeatedly stay under `.agents/plans/reusable/`.
4. **Execution**: Approved one-off plans are executed, and once implemented, verified, and tested, the IPD is moved to the terminal directory `.agents/plans/executed/`.
5. **Retirement (superseded / not-executed)**: A plan that is never run is NOT filed under `executed/` (that would falsely claim implementation). Instead, prepend a `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` header and `git mv` it to `.agents/plans/superseded/` (replaced by a better/subsequent plan) or `.agents/plans/not-executed/` (deliberately decided against, no replacement). Never silently delete a plan; retiring preserves the record and the reason.
<!-- AGENT-PLANS:END -->
