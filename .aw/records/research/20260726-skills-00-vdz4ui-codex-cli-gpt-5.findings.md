---
id: vdz4ui
created: 20260101
set: skills
order: 00
topic: []
model:
kind: findings
status: reference
outcome: informational
summary: Migrated from 20260726-skills-00-vdz4ui-codex-cli-gpt-5.findings.md.
consumed-by: []
---
# Codex CLI and GPT-5.6 fit: preliminary findings

Date: 2026-08-07
Scope: Read-only repository review, focused on use with GPT-5.6 in Codex CLI. No repository behavior was changed.

## Bottom line

The workflow content is broadly usable in Codex because the repository has `AGENTS.md` and tool-agnostic workflow bodies. The largest practical gap is invocation and packaging: OpenCode and Claude Code receive 21 generated native command shims each, while Codex receives neither a plugin nor any `SKILL.md` descriptors. A Codex user must remember and formulate the fallback, "Read and execute `.agents/workflows/<body>`," every time.

The highest-value improvement would be a Codex plugin/skills distribution path that exposes a small set of workflow entry points, backed by the existing workflow files. Do not duplicate the workflow logic.

## Findings and recommendations

### 1. Add a first-class Codex package

Evidence:

- `.opencode/commands/` and `.claude/commands/` each contain 21 generated workflow shims.
- The repo contains no `plugin.json` and no `SKILL.md`.
- The current Codex CLI exposes `codex plugin add`, `codex plugin marketplace`, and `codex plugin list`.
- The installer explicitly regards Codex as a universal-fallback host in `agent_workflows/engine.py`.

Recommendation:

- Create a personal/public Codex plugin with a compact manifest and skills for the core workflows.
- Start with `getting-started`, `list-workflows`, `assess`, `plan-review`, `verify`, `release-review`, and `setup-repo`. Keep parameter parsing in the skill instructions thin and defer to the existing workflow body.
- Offer the plugin separately from `aw install` first. Once validated, let the installer optionally generate or install repo-local Codex skills if that is a supported, stable surface.

Why it matters:

- It removes the recall and wording burden at the point of use.
- It lets Codex discover workflows on demand rather than relying on a broad, always-loaded instruction block.

Estimated work: Medium. The difficult part is validating the plugin format and current Codex discovery behavior, not rewriting workflow content.

### 2. Correct the Codex conformance matrix before treating it as evidence

Evidence from `.agents/workflows/conformance/tools/host_matrix.json`:

- Codex is described as supporting `.agents/skills/{skill_name}/SKILL.md` and global `.codex/skills/{skill_name}/SKILL.md`.
- Its diagnostic commands are `codex status` and `codex inspect-context`.
- Its execution template is `codex exec --repo {target_repo} ...`.

Observed against the installed Codex CLI:

- `codex exec --repo /tmp` fails: `unexpected argument '--repo' found`.
- The general CLI supports `-C, --cd <DIR>` for a working root.
- `codex status` and `codex inspect-context` are not listed subcommands. In noninteractive execution, they are treated as a prompt and fail because stdin is not a terminal, so they are not useful diagnostics.

Recommendation:

- Re-probe every claimed Codex behavior on a version-pinned CLI and record the exact CLI version and commands used.
- Replace stale diagnostics and templates with commands that exist, such as `codex --version`, `codex doctor`, `codex features list`, and a noninteractive `codex exec -C <repo> ...` probe when authorized.
- Make unsupported or unverified entries explicit instead of labeling them supported.

Estimated work: Small to medium, but it should precede plugin or installer design.

### 3. Make `AGENTS.md` leaner and move conditional policy out of always-loaded context

Evidence:

- `AGENTS.md` is 51 lines, 1,157 words, and 8,157 bytes.
- Its managed `aw:pointer` block contains workflow discovery plus prompt-production, durable-research, inter-agent communications, execution/commit, leak-sanitizer, human-question, and IPD-lifecycle policy.
- Several rules are only relevant after an agent selects a workflow or begins a particular artifact type.

GPT-5.6-specific rationale:

- Official OpenAI model guidance recommends leaner prompts, stating each instruction once, exposing only relevant tools, and moving conditional detail to task-specific context. It also recommends a compact autonomy policy with clear boundaries.

Recommendation:

- Retain only workflow discovery, a compact autonomy boundary, the inbox check pointer, and a pointer to governance details in `AGENTS.md`.
- Move IPD mechanics, research artifact naming, leak-sanitizer commands, and prompt handoff rules into the relevant workflow bodies or a referenced governance file.
- State the mutation rule once in terms compatible with normal Codex use: inspect/report for review and planning; make in-scope local changes for an explicit change request; require confirmation for external, destructive, costly, or scope-expanding actions.

Important caution:

- Preserve hard requirements that materially protect releases. The goal is to remove duplication and unconditional detail, not relax safety or evidence standards.

Estimated work: Small implementation, medium validation. Use a fixed set of representative tasks to check that behavior and outcomes do not regress.

### 4. Document a Codex-specific install and use path

Evidence:

- The README includes Codex in the generic fallback row, but the generated command artifacts are only for OpenCode and Claude Code.
- `AGENTS.md` addresses "Antigravity & Other Agents," rather than naming Codex and its actual entry points.

Recommendation:

- Add a Codex-specific install/use path with a copy-pasteable plugin or skills command.
- Document the fallback only as a fallback.
- Add a small compatibility table: tested Codex version, supported install mode, activation phrase or skill name, and validation command.

Estimated work: Small once item 2 establishes the actual support contract.

### 5. Add behavioral evaluation, not merely file-generation tests

Current coverage is primarily unit/fixture coverage for workflow files, installer output, and the conformance harness. That is useful but does not demonstrate that Codex discovers and follows the intended workflow.

Recommendation:

- Add a tiny disposable fixture repository plus 5 to 8 end-to-end acceptance cases run with a pinned Codex CLI.
- Examples: discovery of `getting-started`; argument handling for `assess security src`; read-only behavior for `release-review-plan`; refusal to execute an unapproved IPD; correct evidence capture by `verify`.
- Evaluate task success, required output fields, unintended mutation, workflow selection, token use, and latency. Run these before and after instruction slimming or packaging changes.

Estimated work: Medium. It provides the evidence needed to tune GPT-5.6 behavior safely.

## Suggested sequence

1. Re-probe and repair the Codex conformance matrix.
2. Prototype one Codex skill or plugin entry point for `getting-started` and one parameterized flow, `assess`.
3. Add the disposable end-to-end acceptance suite.
4. Slim `AGENTS.md` using those evaluations as the guardrail.
5. Expand the plugin to the remaining core workflows and document the Codex path.

## Sources consulted

- Repository: `AGENTS.md`, `README.md`, `.agents/workflows/index.md`, `agent_workflows/engine.py`, `.agents/workflows/conformance/tools/host_matrix.json`, existing command-shim directories, and Codex CLI help.
- Official OpenAI documentation: [Model guidance for GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model). Relevant guidance covers lean prompts, clear autonomy boundaries, intentional reasoning effort, and measuring quality, completeness, token use, latency, and cost on representative tasks.

## Non-findings

- No code, configuration, or documentation was changed as part of the initial review.
- No active files existed in either `.agents/comms/local/inbox/` or `.agents/comms/shared/inbox/`.
