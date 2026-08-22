---
id: f6i3z2
created: 20260821
set: awoptimize
order: 02
topic: [evidence, provenance, experiments]
model:
kind: reference-research
status: intake
outcome: none-yet
summary: Evidence and source appendix: source ledger, repository evidence, experiment ledger, unverified claims, and probes
consumed-by: []
---

# Agent Workflows Optimal Architecture: Evidence and Source Appendix

- Research date: 2026-08-21
- Repository: `fariello/agent-workflows`
- Reviewed ref: default branch `main`
- Reviewed commit: `a2110e96b980fbf778027f1676a73774cb819292`
- Commit date recorded by Git: 2026-08-20T17:33:16-04:00
- Evidence policy: documented facts, repository observations, executed probes, and inferences are labeled separately. A source saying that a feature exists is not evidence that it works in this repository.

## 1. Source ledger

All web sources were accessed 2026-08-21. “Current page” means the publisher supplied no durable publication date on the reviewed page.

| Claim ID | Source | Publisher / page date | Claim type | Claims used |
|---|---|---|---|---|
| OAI-01 | [GPT-5.6 Sol model](https://developers.openai.com/api/docs/models/gpt-5.6-sol) | OpenAI / current page | Official documentation | Exact public model name/ID and Codex-oriented positioning. |
| OAI-02 | [Build skills](https://learn.chatgpt.com/docs/build-skills) | OpenAI / current page | Official documentation | Skill packages use progressive disclosure and can bundle instructions, scripts, references, and assets. |
| OAI-03 | [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | OpenAI / current page | Official documentation | Hierarchical repository instructions, nested overrides, project-document budget/diagnostics. |
| OAI-04 | [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | OpenAI / current page | Official documentation | Codex subagent configuration and role delegation. |
| OAI-05 | [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) | OpenAI / current page | Official documentation | Scriptable Codex invocation. |
| OAI-06 | [App server](https://learn.chatgpt.com/docs/app-server) | OpenAI / current page | Official documentation | Eventful programmatic integration boundary. |
| OAI-07 | [Codex prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) | OpenAI / current page | Official maintained example | Prompt and tool-use guidance; not used as evidence of model-wide success rates. |
| GGL-01 | [Gemini 3.7 Flash](https://ai.google.dev/gemini-api/docs/latest-model) | Google / current page | Official model documentation | Exact ID `gemini-3.7-flash`; Medium is a thinking level; documented 1M input, 64K output, and low/medium/high thinking levels. |
| GGL-02 | [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/) | Google / 2026-04-30 | Official host documentation | `.gemini/skills` or `.agents/skills`, Agent Skills packaging, progressive disclosure, `skill://`. |
| GGL-03 | [Gemini CLI subagents](https://geminicli.com/docs/core/subagents/) | Google / current page | Official host documentation | Isolated context/toolset and non-recursive subagents. |
| GGL-04 | [Gemini CLI headless mode](https://geminicli.com/docs/cli/headless/) | Google / 2026-03-10 | Official host documentation | `-p`, JSON/stream-JSON, and exit behavior. |
| GGL-05 | [Gemini CLI git worktrees](https://geminicli.com/docs/cli/git-worktrees/) | Google / 2026-03-20 | Official host documentation | Experimental worktree isolation. |
| GGL-06 | [GEMINI.md context files](https://geminicli.com/docs/cli/gemini-md/) | Google / 2026-06-18 | Official host documentation | Hierarchical context and on-demand file inclusion. |
| ANT-01 | [Claude Opus 5](https://www.anthropic.com/claude/opus) | Anthropic / current page | Official model page | Exact public product/model name and API identifier `claude-opus-5`. |
| ANT-02 | [Claude Code skills](https://code.claude.com/docs/en/skills) | Anthropic / current page | Official host documentation | Skills as the reusable command successor; isolated/forked skill execution and bundled resources. |
| ANT-03 | [Claude Code subagents](https://code.claude.com/docs/en/sub-agents) | Anthropic / current page | Official host documentation | Separate context/tools/permissions, worktree isolation, fresh/fork context options. |
| ZAI-01 | [GLM-5.3](https://docs.z.ai/guides/llm/glm-5.3) | Z.ai / current page | Official model documentation | Exact model name; documented 1M context, 128K output, tool/structured output, reasoning levels, max coding recommendation. |
| KIRO-01 | [Kiro skills](https://kiro.dev/docs/skills/) | AWS/Kiro / current page | Official host documentation | `.kiro/skills`, `skill://`, and progressive disclosure. |
| KIRO-02 | [Kiro custom agents](https://kiro.dev/docs/custom-agents/) | AWS/Kiro / current page | Official host documentation | Custom-agent packaging and tool/permission scoping. |
| KIRO-03 | [Kiro subagents](https://kiro.dev/docs/custom-agents/subagents/) | AWS/Kiro / current page | Official host documentation | Isolated context/tools/permissions and parallel subagents. |
| KIRO-04 | [Kiro headless mode](https://kiro.dev/docs/cli/headless/) | AWS/Kiro / current page | Official host documentation | `kiro-cli chat --no-interactive` and no mid-session input. |
| KIRO-05 | [Kiro CLI 2.x reference](https://kiro.dev/docs/cli/2x-reference/) | AWS/Kiro / current page | Official host documentation | 2.x surface and 3.0 migration boundary. |
| OC-01 | [OpenCode CLI](https://opencode.ai/docs/cli/) | Anomaly/OpenCode / 2026-08-20 | Official host documentation | `opencode run`, JSON format, variants, fork, server behavior. |
| OC-02 | [OpenCode agents](https://opencode.ai/docs/agents/) | Anomaly/OpenCode / 2026-08-20 | Official host documentation | Primary/subagent definitions and experimental background agents. |
| OC-03 | [OpenCode skills](https://opencode.ai/docs/skills/) | Anomaly/OpenCode / 2026-08-20 | Official host documentation | Skill discovery paths and native skill loading. |
| OC-04 | [OpenCode rules](https://opencode.ai/docs/rules/) | Anomaly/OpenCode / 2026-08-20 | Official host documentation | `AGENTS.md` and external instruction configuration. |
| OC-05 | [OpenCode commands](https://opencode.ai/docs/commands/) | Anomaly/OpenCode / 2026-08-20 | Official host documentation | `.opencode/commands`, arguments, and file references. |

## 2. Repository evidence ledger

All references are against commit `a2110e96b980fbf778027f1676a73774cb819292` unless labeled as newly authored pending-plan evidence.

| Evidence ID | Exact location | Type | Observation / claim supported |
|---|---|---|---|
| REPO-01 | `.aw/system/workflows/index.md:3-26` | Repository-observed | Version source, on-demand design, one-line always-loaded pointer, manifest/shim contract. |
| REPO-02 | `.aw/system/workflows/index.md:28-91` | Repository-observed | Sixty manifest command rows, including shared assess and advise bodies and deliberate plan-review parity. |
| REPO-03 | `agent_workflows/ipd_lint.py:7-17`, `:786-790` | Repository-observed | Lint proves only structural/state conformance and explicitly excludes semantic/evidence authenticity claims. |
| REPO-04 | `agent_workflows/ipd_lint.py:660-705` | Repository-observed | Pre-execution blocks open blocking questions; pre-transition checks performed/pass/non-empty fields without authenticating evidence. |
| REPO-05 | `.aw/system/workflows/verify-execution/verify-execution.md:74-129` | Repository-observed | Actual diff, intent audit, real rerun, output/exit capture, and incomplete-on-unverified rules. |
| REPO-06 | `.aw/system/workflows/plan-review-long/plan-review-long.md:35-60` | Repository-observed | Kernel/JIT loading and read-only parallel lanes with serial synthesis/mutation. |
| REPO-07 | `.aw/system/workflows/release-review/00-run-protocol.md:35-81` | Repository-observed | MUST/SHOULD tiers, attention ordering, optional phase isolation, and limits of summary-grounding. |
| REPO-08 | `.aw/system/workflows/release-review/00-run-protocol.md:5-31` | Repository-observed | Authority, run-record, exclusion, and self-modification rules. |
| REPO-09 | `.aw/system/workflows/assess-all/assess-all.md:8-15`, `:32-74` | Repository-observed | Lens catalog is the source of truth; aggregate orchestration, synthesis, partial-coverage honesty, and one-IPD output. |
| REPO-10 | `.aw/system/workflows/conformance/operator-protocol.md:3-8`, `:18-45` | Repository-observed | No tier ships without live host/version evidence; isolated temp home and deterministic render protocol. |
| REPO-11 | `.aw/system/workflows/conformance/tools/host_matrix.json:1-151` | Repository-observed | Seed command/capability assumptions requiring live verification. |
| REPO-12 | `tools/agy_run.py:733-749` | Repository-observed | The current skeptical audit uses the exact execution session ID. |
| REPO-13 | `DECISIONS.md:130-165` | Repository-observed | Instruction density, structural forcing, JIT reference material, and single-set/no-fork decisions. |
| REPO-14 | `DECISIONS.md:1866-1880` | Repository-observed | Single-file and modular plan-review A/B decision and parity burden. |
| REPO-15 | `DECISIONS.md:1922-1926` | Repository-observed | False executed-plan and fabricated-walkthrough failure category. |
| REPO-16 | `DECISIONS.md:1959-1988` | Repository-observed | Parallel-agent overscope/false completion and actual-diff verification decision. |
| REPO-17 | `DECISIONS.md:2006-2011` | Repository-observed | Execution contract and suggestive n=1 Flash findings; supports controlled evaluation, not a general model law. |
| REPO-18 | `DECISIONS.md:2132-2137` | Repository-observed | Read-only auto-parallel lanes and coordinator sole-writer policy. |
| REPO-19 | `DECISIONS.md:2317-2327` | Repository-observed | Phase 0 conformance is deterministic scaffolding plus operator-run launches; dual checklist rationale and size guidance. |
| REPO-20 | `.aw/records/plans/executed/20260809-awlayout-00-az9912-aw-project-layout-orchestrator.ipd.md:18-23` | Repository incident | Eleven Gemini-executed children, green same-session audits, independently found red suites, two material defects, and repaired final suite. |
| REPO-21 | `.aw/records/plans/executed/20260809-awlayout-00-az9912-aw-project-layout-orchestrator.ipd.md:183-229` | Repository incident | Per-child falsifiable evidence, actual corrections, and whole-Set validation details. |
| REPO-22 | `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:1-125` | Repository-observed | Fail-closed lifecycle and terminal transaction authority. |
| REPO-23 | `agent_workflows/engine.py` generated workflow/host shim logic and corresponding `tests/` parity/install fixtures | Repository-observed | Existing generator foundation can be extended instead of replaced by hand-maintained adapters. |

### Inventory reconciliation

- Manifest invocations: **60** rows.
- Non-cache files under `.aw/system/workflows/`: **151**.
- Markdown files under that tree: **141**.
- Approximate non-cache line count: **13,589**.
- The report enumerates every manifest command and separately classifies conformance tools, templates, README files, lenses, personas, and step modules.
- No orphaned invokable command was identified. The main risks are mutable parity copies, generated-shim assumptions, and non-invokable conformance assets being misread as observed capability evidence.

## 3. Experiment and command ledger

### EXP-01 - Requested executable availability probe

- Type: executed local capability probe.
- Environment: the supplied Work Mode Linux workspace; repository pinned at the reviewed commit.
- Exact command class: shell `command -v` checks for `codex`, `opencode`, `kiro-cli`, `gemini`, `claude`, and `agy`.
- Input: executable names above; no credentials and no network mutation.
- Expected: record presence without installing or launching anything.
- Result: all six were **NOT_INSTALLED**.
- Exit interpretation: the aggregate inspection completed successfully; individual absence is a result, not a command failure.
- Limitation: this says only that the binaries were unavailable in this workspace. It says nothing about their general availability or behavior.
- Artifact path: this appendix; no raw secret-bearing environment dump was retained.

### EXP-02 - Focused deterministic conformance and `agy` runner tests

- Type: executed offline repository test.
- Exact command: `python3 -m unittest tests.test_conformance_harness tools.test_agy_run -v`
- Configuration: repository root, Python from the supplied environment, no model calls or credentials.
- Inputs: committed conformance-harness and mocked `agy` fixtures.
- Expected: all deterministic fixture and mocked runner tests pass; audit-session behavior is observable.
- Actual summary: **Ran 47 tests; OK; exit 0**. The mocked runner output included `Auditing ... in the same session...`, consistent with `tools/agy_run.py:733-749`.
- Limitation: validates only repository code and mocks. It does not prove any live host command, model behavior, or real session independence.
- Artifact path: committed test modules plus this summary.

### EXP-03 - IPD scaffolding and synchronization

- Type: executed deterministic authoring tool run.
- Configuration: the repository's actual `aw` Python module at the reviewed commit.
- Inputs: Set `awoptimize`, one orchestrator Order 00, eight child titles Orders 01-08.
- Expected: canonical bullet metadata, generated filenames/IDs, stable E/V pairs.
- Result: nine plans created in `.aw/records/plans/pending/`; `aw ipd sync` assigned and preserved all E/V identifiers; exit 0 for the successful authoring commands.
- Limitation: creation and synchronization do not establish plan semantic quality or future execution success.
- Artifact paths: the nine IPDs in this package.

### EXP-04 - IPD author checkpoint lint

- Type: executed deterministic structural/state validation.
- Exact command: `python3 -m agent_workflows ipd lint --phase author --agent .aw/records/plans/pending/20260821-awoptimize-*.ipd.md`
- Expected: every new plan has `DISPOSITION conforming` with E/V bijection and valid metadata/DAG fields for the author checkpoint.
- Actual result: all nine files reported **DISPOSITION conforming**; aggregate exit **0**.
- Interpretation boundary: per REPO-03, this does not prove semantic coverage, correctness, evidence authenticity, or execution.
- Artifact paths: the nine IPDs and the final validation summary in Section 6.

### EXP-05 - Live behavioral ablations

- Type: **deferred, not executed**.
- Reason: none of the requested CLI hosts was installed; no model credentials or spending authorization was available; the prompt forbids installation or material cost without explicit authorization.
- Exact input families: the 15-30 requirement, monolith/JIT, same/fresh context, self/independent verification, prose/schema, raw-evidence, failed-tool, overlooked item, surface-only implementation, weakened-test, compaction/resume, parallelism, injection, and approval/scope cases specified in report Section 14.
- Expected behavior and scoring: versioned golden requirements, hidden checks, terminal-claim reconciliation, repeated trials, exact host/model/config capture, Wilson intervals.
- Result: **pending**.
- Artifact path: report Section 14 and IPD `20260821-awoptimize-06-ozlus1-behavioral-benchmark-and-regression-harness.ipd.md`.

## 4. Unverified claims and exact probes

| Unverified claim | Why unverified | Exact probe required |
|---|---|---|
| GPT-5.6 Sol instruction coverage, persistence, evidence discipline, and optimal reasoning level in Codex CLI | Official interfaces are documented; no live CLI/model run occurred. | In an isolated repo, run corpus-v1 through pinned Codex CLI/model/settings with JSON events; 10 screening and 30 promotion trials per ablation; capture compaction and approval events. |
| Gemini 3.7 Flash Medium has a higher false-completion rate than other target models | One repository incident lacked exact durable model/config and is not a controlled comparison. | Run paired randomized corpus trials in Gemini CLI and `agy` at medium, then high where approved; same tasks/seeds, hidden checks, fresh verifier; report rates and intervals. |
| Claude Opus 5 benefits from forked workers or cross-model review on this corpus | Host mechanics are documented, outcome benefit is not. | Compare single, forked worker, fresh worker, and fresh verifier cells in pinned Claude Code; capture context mode and worktree behavior. |
| GLM 5.3 structured outputs and max reasoning satisfy the runtime schemas reliably | Vendor documentation is not a local observation. | Use the intended exact API/CLI adapter; validate every result against `result.schema.json`; record repair attempts, tool errors, and max/high comparison. |
| `agy` can create a genuinely fresh independent session, stream progress, resume, cancel, or safely run background tasks | Current repository runner only proves same-session turn two; exact upstream version was not available. | Pin executable/version, inspect `--help` and official source, run two nonce-separated sessions in an isolated repo, verify conversation IDs/events/cancellation and filesystem effects. |
| Seed commands in `host_matrix.json` are supported | D113 identifies them as Phase 0 scaffold assumptions. | For each exact host/version, scaffold an isolated temp home, render commands, run them, record transcripts/exits/side effects, and validate the evidence report. |
| Native skill autoactivation consistently selects the intended workflow across hosts | Discovery syntax is documented; activation quality is behavioral. | Positive, negative, paraphrase, collision, nested-instruction, and injection trigger suite with skill enabled/disabled; measure precision/recall and task outcome. |
| Read-only parallel review improves quality enough to offset synthesis cost | Repository policy is plausible but not controlled evidence. | Compare serial and parallel lanes on the same multi-plan/audit tasks; measure unique true findings, false positives, conflicts, latency, token/cost, and synthesis misses. |
| Fresh contexts always improve verification | Isolation may lose tacit intent. | Compare same-session, forked, and fresh verifier packets with/without decision excerpts; score hidden intent and false completion. |

## 5. Disagreements and interpretation rules

1. The repository's seeded host matrix contains apparent support booleans and commands, while the operator protocol and D113 say the live launches remain unperformed. The protocol governs: these are **unverified probe inputs**, not support evidence.
2. Official model/host pages document capacity and mechanisms, not successful instruction coverage or honest validation. This report does not translate context-window size into reliability.
3. The repository incident specifically implicates its Antigravity/Gemini execution route and same-session audit. It supports stricter controls and a benchmark hypothesis, not a model-wide stereotype.
4. Vendor-recommended reasoning levels are starting configurations, not benchmark conclusions. Exact profiles remain provisional until corpus results exist.

## 6. Final validation record

This section is intentionally completed only after all artifacts are fixed. It records command summaries rather than predicted outcomes.

| Check | Command / method | Result | Exit |
|---|---|---|---:|
| Focused deterministic tests | `python3 -m unittest tests.test_conformance_harness tools.test_agy_run -v` | Ran 47 tests; OK | 0 |
| Full repository tests | Two full discovery attempts, fail-fast diagnosis, and bounded module segments | **Not green / limited:** 1,244 tests discovered; 1,229 separately rerun; eight failures confined to `tests.test_awmigrename` (1) and `tests.test_awnaming_grammar_and_producers` (7); two skips; 15 `tests.test_run_checks` cases could not be separately launched after sandbox approval transport rejection. The two full attempts lost process transport before terminal summaries. | 1 for reproduced failure; transport-limited full run |
| Nine-IPD author lint | `python3 -m agent_workflows ipd lint --phase author --agent <each generated IPD>` | 9/9 `DISPOSITION conforming` | 0 |
| Markdown/repository conformance | `python3 /tmp/validate_awoptimize_docs.py <package> <repo>` and `python3 -m agent_workflows attention --check` | PASS: 12 Markdown files before MANIFEST, nine draft/pending IPDs, E/V pending-state checks, Sections 1-18, local links, UTF-8/LF/fences/whitespace/dash checks, 60/60 manifest command coverage; attention view valid | 0 / 0 |
| Leak/secret sanitization | repository `check-local-leaks`; package built-in working-tree secret/PII scan with entropy-only false positives disabled; explicit local identity pattern scan | PASS: repo local leaks empty; package zero non-entropy secret/PII candidates; no home/workspace path or email pattern. External scanners were not installed. | 0 / 0 / 0 |
| Archive member listing | `tar -tzf agent-workflows-optimal-architecture-ipds.tgz` | PASS: exactly one top-level `agent-workflows-optimal-architecture-ipds/` directory, MANIFEST, three reports, and nine IPDs; no cache, `.git`, dependency, credential, or unrelated member | 0 |
| Manifest member verification | `python3 /tmp/verify_awoptimize_archive.py agent-workflows-optimal-architecture-ipds.tgz` | PASS: 13 file members; membership, raw byte sizes, 12 ordinary SHA-256 digests, and the documented canonical MANIFEST self-digest all verified from archive bytes | 0 |
| Deliverable presence | exact filename/count/type checks against package and archive | PASS: report, index, evidence, MANIFEST, nine IPDs, and tgz present | 0 |

No pending row may be described as passed in the delivery message. The final residual audit and actual command outputs replace these rows before packaging.

## 7. Residual-obligation audit against the controlling prompt

Status vocabulary: **satisfied** means the requested research/design/artifact exists and was checked; **pending empirical** means the exact live model/host experiment was correctly not run and has a reproducible probe; **limited** means a validation was attempted but the environment prevented a clean result. A pending empirical or limited row is never silently counted as passed.

### 7.1 Investigation method

| Prompt item | Status | Evidence |
|---|---|---|
| Method 1.1 - every file under the workflow tree | satisfied | Complete filesystem enumeration: 151 non-cache files, 141 Markdown files, 13,589 lines; report Section 4 classifies invocations, steps, templates, lenses, personas, helpers, README/MANIFEST, and conformance assets. |
| Method 1.2 - manifest and generated host shims | satisfied | Report Sections 4, 5, and 10; REPO-01, REPO-02, REPO-23. |
| Method 1.3 - root architecture/principles/decisions/contributing/release docs | satisfied | Repository audit used `AGENTS.md`, `ARCHITECTURE.md`, `GUIDING_PRINCIPLES.md`, `DECISIONS.md`, `CONTRIBUTING.md`, README/changelog/install/release material; material findings cite decisions directly. |
| Method 1.4 - IPD templates/spec/linter/scaffold/sync/tests | satisfied | REPO-03, REPO-04, REPO-19; nine plans were scaffolded, synced, and author-linted using repository code. |
| Method 1.5 - installer/engine/generated adapters/always-loaded instructions | satisfied | Report Sections 4, 5, 10, 12, 15; REPO-01, REPO-23. |
| Method 1.6 - verification/execution/audit/sanitization/evidence tooling | satisfied | REPO-03 through REPO-12; focused tests and scans in Sections 3 and 6. |
| Method 1.7 - Kiro/OpenCode/Codex/Claude/Gemini/`agy`/other adapters | satisfied as documented research; live behavior pending | Report Sections 9-10; OAI/GGL/ANT/ZAI/KIRO/OC source ledgers; exact probes in Section 4. |
| Method 1.8 - executed/corrective plans/records/commits | satisfied | REPO-15 through REPO-21, especially the `awlayout` incident record. |
| Method 1.9 - parity/generated/template/manifest/adapter tests | satisfied | Relevant test modules inventoried; plan-review parity and generator findings in report; segmented suite evidence in Section 6. |
| Method 1.10 - active specs/plans/backlog/TODO/staged prompts | satisfied | Repository-wide search and record review informed the inventory and IPD non-goals; no directly competing active implementation was treated as complete. |
| Workflow inventory required fields | satisfied at family/file level | Report Section 4 records path, purpose, artifact form, mutation, orchestration, deterministic helper, adapter, risk, exposure, parity, and disposition for every manifest row; shared family rows prevent repetitive false precision. |
| Method 2 - source hierarchy/current facts/exact names | satisfied | Section 1 source ledger; report Sections 2, 3, 9, 10, and 18. Facts are labeled official, repository-observed, experiment, inference, or unverified. |
| Method 3 - focused empirical probes | limited / pending empirical | Offline availability, conformance/runner, scaffold/sync/lint, suite, and sanitization probes ran. Paid/live model ablations did not run because binaries/credentials/budget were unavailable; EXP-05 and Section 4 specify exact reproducible designs. |

### 7.2 Core question A - audit current workflow design

| Item | Status | Evidence |
|---|---|---|
| A1 precise/testable/enforceable instructions | satisfied | Report Sections 4-5. |
| A2 ambiguous/duplicated/contradictory/buried/broad instructions | satisfied | Report Section 5.2, especially parity, seeded capability claims, and prose-driven state. |
| A3 obligations that should become code/schema | satisfied | Report Sections 5-7 and 12. |
| A4 always-reread kernel material | satisfied | Report Sections 7-8 and 13. |
| A5 just-in-time/optional reference material | satisfied | Report Sections 7-8; REPO-06, REPO-07, REPO-13. |
| A6 workflows too monolithic | satisfied | `release-review`, plan-review parity, lifecycle/release/setup/aggregate findings in Sections 4-5. |
| A7 needless fragmentation | satisfied | Assess/advise aliases and generated lens/persona package recommendation. |
| A8 outcome gates versus self-attestation | satisfied | Sections 5-6; REPO-03 through REPO-05. |
| A9 unchecked evidence weakness | satisfied | Linter pre-transition boundary in Sections 5-6. |
| A10 tests pass while intent fails | satisfied | Threat matrix, clean-room verifier, hidden tests, test-integrity review. |
| A11 shim context/argument/dependency loss | satisfied | Host matrix and adapter schema/parity tests. |
| A12 mutable copies/source of truth | satisfied | Plan-review A/B and generated-adapter recommendation. |
| A13 boundary/mutation/commit/lifecycle consistency | satisfied | Report Sections 4, 5, 8, and 15; child IPDs preserve human release boundary. |
| A14 run-record restart/audit usefulness | satisfied | Report Sections 5.2, 6, 8.3, and 12.3. |
| A15 repository evidence per finding | satisfied | Report Section 5 and repository ledger. |
| Required per-workflow disposition | satisfied | Complete 60-row report Section 4 table plus non-invokable assets. |

### 7.3 Core question B - artifact taxonomy

| Item | Status | Evidence |
|---|---|---|
| Operational definitions for 12 artifact types | satisfied | Report Section 7 table covers always-loaded instructions, workflow, skill, shim, prompt, helper, schema, lens/persona, orchestrator, child, verifier, and evidence bundle. |
| Decision dimensions: discovery, precedence, portability, context, tools, capability, versioning, tests, updates, security, interaction, resume, recovery | satisfied | Report Section 7 matrix/rule and Section 8 contracts. |
| B1 one portable source + adapters | answered yes | Recommended deterministic hybrid, Sections 7, 11, 12. |
| B2 universal core + profiles | answered yes, profiles constrained | Sections 6, 9, 11, 12. |
| B3 separate model forks | answered no by default | Sections 5, 7, 11; semantic-digest gate in Orders 01/05. |
| B4 native skills wrapping canonical workflows | answered yes selectively | Sections 7, 10, 12; Orders 05/07. |
| B5 hybrid architecture | selected | Weighted analysis in Section 11. |
| Exact skill requirements per supported environment | satisfied as implementation design; live discovery pending | Report Sections 7, 10, 12; official source ledger; Order 05. |

### 7.4 Core question C - false-completion controls

| Item group | Status | Evidence |
|---|---|---|
| Requirement omission, partial/cosmetic work, easier substitution | satisfied | First three rows of report Section 6 threat matrix. |
| Self-authored evidence, unrun/stale/nonzero tests, baseline blame | satisfied | Section 6 rows 4-6 and evidence envelope. |
| Test weakening/deletion/mocking and memory-only validation | satisfied | Section 6 test-integrity and clean-room controls. |
| Wrong tree/commit/environment/artifact and summary/log disagreement | satisfied | Section 6 evidence-envelope and compiler-derived report controls. |
| Context-boundary loss, early stopping, child-report trust, compaction | satisfied | Section 6 residual/runtime/worker rows. |
| Tool errors, parallel overwrite, approval/security/no-push bypass | satisfied | Section 6 typed failure, single-writer, capability-token controls. |
| Acceptance criteria edited after failure | satisfied | Requirement freeze/revision invalidation in Sections 6 and 12. |
| Prevention/detection/recovery distinction | satisfied | Every threat row has all three. |
| Listed stable IDs, E/V, evidence schemas, hashes, baselines, changed-test checks, verifier, intent audit, lint, residuals, terminal status, retry, partial verdict, role separation, sampling | satisfied | Sections 6, 8, 12-14 and Orders 01-06. |
| Broad versus Gemini-specific controls | satisfied without stereotype | Report Section 6 Gemini posture and Section 9; live comparative rate remains pending empirical. |

### 7.5 Core question D - orchestration

| Item | Status | Evidence |
|---|---|---|
| Patterns D1-D10 | satisfied | Report Section 8.2 compares monolith, JIT steps, sequential workers, parallel auditors, clean verifier, four roles, persistent server, stateless packets, cross-model review, and escalation. |
| Quality, isolation, tacit context, coordination, concurrency, permissions, handoff, determinism, observability, restart, cost, suitability, fallback | satisfied | Section 8.2 comparison plus exact contracts in 8.3-8.4. |
| Measurable orchestration thresholds | satisfied, subject to calibration | Section 8.1; Order 06 calibration. |
| Coordinator authority | satisfied | Section 8.3 and Order 04. |
| Worker role/scope/tools/mutation/stop | satisfied | Section 8.3. |
| Minimal immutable context packet | satisfied | Section 8.3. |
| Structured output/evidence references | satisfied | Sections 8.3 and 12.2-12.3. |
| Timeout/heartbeat/cancel/retry/duplicate behavior | satisfied | Section 8.3. |
| Worktree/filesystem isolation and merge policy | satisfied | Section 8.3. |
| Never delegated and coordinator reverification | satisfied | Section 8.3. |
| Human progress and resume/compaction | satisfied | Section 8.3. |
| Exact host session/fork/background mechanisms | documented or explicitly unverified | Report Section 10 and appendix Section 4; `agy` limitations are not inferred. |

### 7.6 Core question E - model and host optimization

| Item | Status | Evidence |
|---|---|---|
| Separate model behavior matrix | satisfied, conservative | Report Section 9 covers exact named models, documented identity/capacity/reasoning, available behavior evidence, safeguards, and exact pending probes. Unmeasured traits are not fabricated. |
| Model instruction/tool/persistence/compaction/planning/checklist/structured-output/negative-constraint/ask/evidence/premature/subagent/effort/cost fields | explicitly documented or marked unverified | Section 9 uses a combined evidence/profile/probe structure to avoid false precision; Section 14 defines every missing measurement. |
| Separate host capability matrix | satisfied | Report Section 10. |
| Host discovery, skills/commands, args, tools/approval, headless, sessions, workers, streaming, compaction, isolation, hooks, output, MCP, deterministic integration, CI, adapter | documented, designed, or explicitly unverified | Section 10 plus official sources and exact probes. No uniform capability is assumed. |
| Model versus host separation | satisfied | Separate Sections 9 and 10 and explicit note. |
| Literal layout/schemas/invocations | satisfied | Report Section 12. |
| Current integration disposition | satisfied | Sections 4, 10, 12, 15 and Order 05. |

### 7.7 Core question F - coding effectiveness lifecycle

| Item | Status | Evidence |
|---|---|---|
| F1-F14 intake through continuous improvement | satisfied | Report Section 13 has twelve consolidated stages covering all fourteen requested phases; planning/decomposition and commit/release are separately addressed. |
| Repository maps, traceability, invariants/non-goals, packets, acceptance criteria, characterization tests, checkpoints, generated checklists, state+Markdown, raw logs, dirty-worktree checks, test integrity, advanced tests, stop/escalate, calibrated status | satisfied | Report Sections 6, 8, 12-14 and IPDs 01-08. |
| Detailed checklist benefit versus context cost | satisfied | Report Section 13 final paragraph; detail distributed across nine IPDs. |

### 7.8 Core question G - evaluation and improvement

| Item | Status | Evidence |
|---|---|---|
| Versioned diverse corpus and hidden checks | satisfied as design | Report Section 14.1; Order 06. |
| Repeats/randomization and exact config | satisfied as design | Section 14.2-14.3. |
| Objective/human metrics, cost/latency/tokens, retention/privacy | satisfied as design | Section 14.3-14.4. |
| Thresholds/statistics/anti-gaming/promotion/rollback/model specificity | satisfied as design; numbers await baseline/human policy | Section 14.3-14.4. |
| All 13 minimum score dimensions | satisfied | Section 14.3 explicitly enumerates them. |
| Per-change smoke versus release live matrix | satisfied | Section 14.4. |
| Exact schemas/layout/fixtures/CI boundaries | satisfied at implementation-design level | Sections 12 and 14; IPD 06 makes exact files executable work. |

### 7.9 Required synthesis decisions

| Item | Answer / evidence |
|---|---|
| 1 orchestrators | Report Sections 4-5: lifecycle, release, execution verification, setup, aggregate assessment; generated stepwise plan review. |
| 2 single-file | Compact bounded workflows in Sections 4-5. |
| 3 skills | Thin native discovery/execution packages, not semantic authority; Sections 7, 10, 12. |
| 4 deterministic obligations | Schema, compiler, ledger, runtime, capability registry, CI; Sections 5-7 and 12. |
| 5 core/profiles/adapters/forks | One core + restricted profiles + thin adapters; no semantic forks. |
| 6 fresh/fork context | Report Sections 8.1 and 8.4. |
| 7 different-model verification | Risk- and benchmark-gated, never assumed; Section 8.4. |
| 8 parallel versus serial | Read-only/disjoint isolated work only; coordinator mutation/integration serial. |
| 9 progress | Ledger event summaries with explicit phase/residuals; no green partial status. |
| 10 minimum evidence | Report Section 6 evidence envelope. |
| 11 unavailable/timeout/failure | `blocked`/`failed`, typed retry/escalation, never success. |
| 12 first implementation | Orders 01-04 behind compatibility/shadow gates. |
| Three alternatives + conservative/balanced/ambitious + weighted/sensitivity | satisfied | Five alternatives, weights, scores, and alternate weighting in report Section 11. |

### 7.10 Deliverables, quality rules, and completion gate

| Requirement | Status | Evidence |
|---|---|---|
| Deliverable 1 report, required Sections 1-18 | satisfied | `agent-workflows-optimal-architecture-research.md`. |
| Deliverable 2 orchestrator + 6-9 children | satisfied | One orchestrator plus eight children, scaffolded/synced/linted, all draft/pending. |
| IPD requirements 1-23 | satisfied at authoring checkpoint | Each IPD has canonical metadata, bounded scope, dependencies, atomic E/V map, pending evidence, tests/security/rollback/docs/non-goals/open questions; orchestrator owns cross-Set checks. Linter is structural only, so report/index/this audit provide semantic cross-check. |
| Deliverable 3 IPD index | satisfied | `agent-workflows-optimal-architecture-ipd-index.md`. |
| Deliverable 4 evidence appendix | satisfied | This file. |
| Deliverable 5 one-root tgz + MANIFEST | satisfied | Section 6 records the listing and archive-byte verification. |
| Required IPD/Markdown/leak/tar/hash/presence commands | satisfied except for the explicitly red/limited repository suite | Section 6 records exact outcomes without claiming the suite green. |
| Quality rules 1-15 | satisfied with stated limitations | Recommendations cite repo/docs/experiments/inference; no prompt-length or subagent absolutism; raw state inspected; unsupported claims unverified; no product code/commit/push; untrusted content treated as data; prevention/detection/recovery separated; confidence and disagreements recorded; one semantic core; correctness precedes cost. |
| Exact commit and complete inventory | satisfied | Header, report Sections 2 and 4. |
| Core questions A-G | satisfied | Report Sections 4-17 and audit Sections 7.2-7.8. |
| All targets covered or unverified with probes | satisfied | Report Sections 9-10; appendix Section 4. |
| Architecture selected comparatively | satisfied | Report Section 11. |
| Files downloadable | pending save/delivery step | Files exist locally; final response provides direct links after save. |
| IPD structural conformance | satisfied | 9/9 author-lint conforming, exit 0. |
| Recommendation/IPD traceability | satisfied | Report Section 17, IPD index, orchestrator V-10. |
| Complete archive/listing/hashes/leak/presence | satisfied | Section 6 records actual passes. |

Residual conclusion before packaging: no research question or requested artifact is silently omitted. Live model/host behavior remains pending empirical by design. The full repository suite is not green in this environment and must be reported as a limitation; it does not invalidate the Markdown-only IPDs' conforming author lint.
