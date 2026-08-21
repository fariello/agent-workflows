# Architecture

How this repository and its main artifact, the `release-review/` framework, are
structured, and why they take this shape. For the dated decision history and the
reasoning behind specific choices, see `DECISIONS.md`. For the values that guide the
work, see `GUIDING_PRINCIPLES.md`.

## What this repository is

`agent-workflows` is a collection of resources for AI-assisted software development. Its
centerpiece is a set of reusable **agent workflows** under `.aw/system/workflows/`. The
flagship, `release-review`, is an executable runbook that an AI coding agent follows
to perform a deep pre-release review of *another* repository and leave it materially
better, with a durable, auditable record of what it did and why.

```text
agent-workflows/
  README.md                 Overview and entry point
  ARCHITECTURE.md           This file
  DECISIONS.md              Dated decision log (the "why")
  GUIDING_PRINCIPLES.md     Values guiding the work
  AGENTS.md                 Pointer to workflow index (mirrored to CLAUDE.md/GEMINI.md if present)
  install-workflows.py/.sh  Installer (human-run bootstrap at root, not a workflow)
  tests/                    Stdlib-unittest self-tests for Python tools and engines
  .aw/                      The canonical physical layout (four roots)
    system/                 The CLI-owned workflow bundle
      VERSION               Framework version (semver, tag-derived); sibling to workflows
      managed-sections.json Manifest of managed block boundaries
      templates/            Initial templates for plans, prompts, and runbooks
      workflows/            Reusable agent workflows (nested bundle root)
        index.md            Workflow manifest (installer reads it to generate shims)
        release-review/     The full, all-concerns pre-release review framework
        plan-review/        Pre-execution plan reviewer (plan-time sibling)
        plan-review-long/   Modular multi-file variant of plan-review (parity)
        assess/             Single-concern assessment harness plus per-concern lenses
          assess.md         Shared harness (assess one concern -> IPD, no auto-execute)
          lenses/           One lens per concern (performance, security, etc.)
          references/       Shared references (e.g. prose-style.md)
          templates/        IPD, run-report, and findings-CSV templates
          tools/            Read-only secret/PII scanner (tree plus history)
        assess-all/         Cross-concern rollup orchestration
        advise/             Interrogate-and-coach harness plus persona charters
          personas/         One charter per expert persona (skeptic, architect, etc.)
        verify/             Evidence layer (proof, not self-report)
        verify-execution/   Post-execution cross-check that a plan was truly done
          tools/            Discovers and runs repo checks; captures evidence
        ipd-lifecycle/      Authoritative execution and terminal-transition gate (aw ipd lint)
        benchmark/          Guided performance benchmarking (informational)
          tools/            Read-only machine/environment capture and diagnosis
        setup-repo/         Guided setup and conformance wizard
          tools/            Deterministic tool-install and plan-naming helpers
        scaffold/           Guided authoring of a new lens/persona/workflow/command
        spec/               Draft a reviewable specification (front of funnel)
        incident/           Blameless post-mortem (reactive operations)
        release-notes/      Version bump and changelog/notes (release discipline)
        migrate/            Assess-and-plan a high-risk migration
        list-workflows/     Toolkit discovery (capabilities and installed version)
        getting-started/    Guided in-agent tour and router for newcomers
    records/                Durable project records (tracked or companion-routed)
      plans/                IPD documents (pending/, executed/, reusable/, superseded/, not-executed/)
      docs/                 Durable reference docs (research/, walkthroughs/, specs/)
      backlog/              Committed lightweight backlog work (open/, done/, parked/)
      comms/                Inter-agent messaging lanes (shared/, local/)
      prompts/              Prompt templates and execution logs
    config/                 Project policy and configuration (config.json, leak allowlist)
    state/                  Local runtime scratch and migration journals (never committed)
  .opencode/commands/       Generated OpenCode shims (one per command)
  .claude/commands/         Generated Claude Code shims (same set)
```

### The Four Physical Roots

The architecture separates concerns into four distinct physical roots under `.aw/`:

1. **System (`.aw/system/`)**: Holds immutable framework assets managed by the installer. The invokable workflow bundle lives nested under `.aw/system/workflows/`, while release metadata (`VERSION`), managed block tracking (`managed-sections.json`), and baseline `templates/` live as siblings at `.aw/system/`.
2. **Records (`.aw/records/`)**: Holds all durable project knowledge produced by workflows and human collaboration. This includes plans, specs, research reports, walkthroughs, backlog records, prompts, and inter-agent communication.
3. **Config (`.aw/config/`)**: Holds project-level configuration (`config.json`) and committed leak-sanitizer allowlists (`local-leaks-allowlist.toml`). Local machine-specific overrides (`local.json`) are strictly gitignored.
4. **State (`.aw/state/`)**: Holds ephemeral runtime state, scratch files, and migration journals. Everything under `.aw/state/` is gitignored and excluded from version control.

Host adapters (`.claude/commands/`, `.opencode/commands/`, `AGENTS.md`) remain at the repository root so native tooling can discover them immediately without modifying host conventions.

### Storage Policies and Presets

Different development environments have distinct visibility requirements. The framework supports four placement presets:

- `private-target` (default): All four roots live inside the target repository and are tracked in git. Ideal for private projects where planning artifacts and code share the same repository.
- `public-private-companion`: System, config, and state live in the target repository (tracked publicly), while `.aw/records/` routes to a separate private companion git repository. Ideal for public open-source projects where internal planning, security assessments, and research must remain private.
- `clean-target`: System and config live in the target repository, while `.aw/records/` routes to `~/.aw/projects/<project-id>/records/` in the user home directory. Keeps the target git repository free of workflow records.
- `local-only`: All roots reside in the target repository but the entire `.aw/` hierarchy is gitignored. Ideal for evaluation or personal use without committing any workflow files.

### Router APIs and Project Context

The framework provides programmatic APIs to query and resolve project context:

- `agent_workflows.project_context.resolve_project_context(repo_path)`: Inspects repository layout, active preset, storage configuration, and returns a structured `ProjectContext` with resolved absolute paths for all four roots.
- `agent_workflows.engine.resolve_source_root()`: Locates the authoritative workflow bundle, descending cleanly into nested `.aw/system/workflows/` or resolving fallback source trees.
- `agent_workflows.storage.validate_storage_boundaries()`: Enforces storage isolation invariants, ensuring records backends cannot perform unintended writes outside their configured boundaries.

### Capability layout (open-ended)

Each workflow is a capability with its own subdirectory under `.aw/system/workflows/`,
even single-file ones, so adding a capability is always "a new subdir plus a row in
`index.md`", never a new top-level directory. The per-tool slash-command shims are
*generated* from the manifest, not hand-maintained. Bodies are tool-agnostic; the
shims and the `AGENTS.md` pointer are the only tool-specific surface. `plan-review`
references `release-review`'s shared policy files (`fix-decision-policy.md`,
`00-run-protocol.md`) as a sibling via `../release-review/`.

## The release-review framework

### Shape: a modular runbook driven by one controlling file

`release-review/README.md` is the single controlling instruction. It points at
`00-run-protocol.md` (global rules) and `fix-decision-policy.md` (the fix policy),
then sequences nine phase files:

```text
README.md            Controlling instruction and orchestration (per-section loop)
00-run-protocol.md   Global rules: personas, Fix Bar summary, MEM/LIVE rules,
                     durable-knowledge objective, IDs, registers, commit/push, safety
fix-decision-policy.md   Canonical Fix Bar (fix-by-default, Remediation-Risk gate)
reference.md         On-demand look-up material (type codes, ID examples, schema/CI lists)
01-current-state.md          Inventory and discovery
02-quality-security-edge-cases.md   Bugs, security, MEM, LIVE
03-tests-regression.md       Test/regression gaps
04-docs-specs-examples.md    Docs and durable-knowledge audit
05-feature-usability-maintainability.md  Features, usability, principles, cold-start
06-compatibility-packaging-release.md    Compatibility, packaging, CI, release
07-implementation.md         The change-making phase (applies the Fix Bar)
08-final-ship-review.md      Readiness verdict, persona sign-off, final report
09-release-execution.md      Post-GO release (push/tag/publish/deploy), user-gated
templates/                   Templates for every run artifact
```

**Why modular files instead of one mega-prompt:** each phase has a focused job, can
be read at the moment it is needed, and (with the per-section execution loop) is
re-read fresh so the agent follows the current phase's rules rather than working from
fading memory of an earlier phase. It also enables an optional phase-isolated
execution mode.

### State: the authoritative run directory

Every run creates `workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped;
`release-review` for the runbook). This directory, not
the chat transcript, is the authoritative record: metadata, inventory,
finding/action registers (CSV), decisions, commands, commits, checkpoints, the
implementation plan, validation results, push plan, the final report, plus
specialized artifacts (schema validation, TODO reconciliation, guiding-principles
assessment, cold-start orientation, persona review) and `section-summaries/`
per-phase reports.

**Why externalize state to files:** long multi-step LLM runs degrade when state lives
only in context. File-based state makes runs recoverable, auditable, committable, and
enables fresh-context phase isolation. This is a load-bearing architectural
decision (see `DECISIONS.md` D7).

### Decision policy: the Fix Bar

`fix-decision-policy.md` is the authoritative statement: fix every finding by default;
defer only when the Remediation Risk of the *fix itself* is Medium-High or higher
across four axes (complexity, usability, security, functionality). Severity is for
reporting; Remediation Risk is for deciding. `00-run-protocol.md` carries only a short
summary plus a pointer, so the policy has exactly one home.

### Reliability design for LLM execution

The framework is large (many always-on obligations). To keep faster/smaller models
from silently dropping rules, the design uses:

- **MUST vs SHOULD tiering** so weaker models shed best-effort depth before mandatory
  outputs.
- **Per-section context contracts** ("read these / produce these / done when") so a
  section is runnable continuously or in fresh context.
- **Per-section exit-gate checklists** so mandatory outputs cannot be silently
  skipped.
- **A context-assembly ordering rule** (front = MUST rules + contract; middle =
  reference + prior registers; end = active section + exit-gate) that exploits
  recency/primacy attention and counters "lost in the middle".
- **An optional phase-isolated execution mode** (fresh context per audit phase, state
  carried by the run directory). Sections 7 and 8 stay continuous because
  implementation and final review benefit from shared evidence; re-loaded register
  summaries do not restore the lived reading of the code, so Section 7 re-opens the
  actual source files cited by High/`LIVE`/`MEM` findings.

### Distribution and Installation

`install-workflows.py` (at the repo root; a human-run bootstrap tool, distinct from the
agent-executed workflows) installs the workflows into a target repo by
copying the live `.aw/system/` tree directly from this repo, conservatively
(manifest-driven, safe in-tree paths, backups, dry-run).

It performs a **clean sync** by default: framework files present in the target that
differ from the source are updated in place (backed up first unless `--no-backup`), and
framework files no longer in the source (renamed or removed) are pruned, so the target
never accumulates stale instruction files and updating is just a re-run. Pruning is strictly scoped to the framework namespace
(`.aw/system/workflows/` plus generated shim files) and never touches
`workflow-artifacts/` run records, user code, or `.aw/records/`.

The installer is git-aware but never commits: installed files are staged with `git add`, pruned
tracked files with `git rm`, untracked files are written/removed on disk, and the
user reviews and commits.

### Migration Architecture (`agent_workflows.layout_migration`)

When migrating from the legacy `.agents/` layout:

1. **Transactional Move Model**: The migration engine moves files rather than copying them. Tracked files are moved using `git mv` (staging the rename and preserving git history); untracked files are moved on the filesystem.
2. **Reversible Journals**: Every moved item is logged to a crash-safe journal under `.aw/state/durable/`. If a migration is interrupted or fails mid-way, `aw migrate-layout resume` continues from the exact failure point, while `aw migrate-layout rollback` restores every item to its original path.
3. **Leftover Disposition**: Files not matching classified records (plans, docs, specs, comms, prompts) are evaluated through a leftover policy: `keep` (leave in place), `remove` (safely delete), or `defer` (record in state for later review). Non-interactive runs default to `defer` and never delete files automatically.

### Inter-agent comms convention (`.aw/records/comms/`)

The installer scaffolds an agent-agnostic **inter-agent comms convention** (DECISIONS D81): a gitignored `local/` lane and a git-tracked `shared/`
lane for leaving filesystem messages between agents (and between an agent and a human). Messages carry a small header envelope (`From`/`To`/`Kind`/`Status`, and
an optional `Not-Before` scheduling gate) over an UNTRUSTED payload; acknowledgements
are a closed enum. The installed pointer block tells agents to check
their inbox at natural boundaries and to treat payloads as untrusted.

### Plan review (plan-time sibling)

`.aw/system/workflows/plan-review/plan-review.md` is a standalone reviewer
for the other end of the lifecycle: it reviews and improves a proposed implementation
plan *before* any code is written, then `release-review` reviews the finished code
before shipping. Catching a flaw on paper is far cheaper than catching it in code. It
reuses shared policy (Fix Bar and personas) from `release-review`, discovers project
principles, and edits planning documents only.

### Assessment workflows (single-concern, IPD-producing)

`.aw/system/workflows/assess/` is a family of focused reviewers that sit between
`plan-review` and `release-review` in the pipeline: each assesses ONE concern deeply
and writes a dated Implementation Plan Document (IPD) into the project's pending-plans
directory (`.aw/records/plans/pending/`) for human approval, rather than fixing in place or auto-executing:

```text
/assess <concern>  ->  IPD in .aw/records/plans/pending/  ->  plan-review (optional)  ->  approval  ->  execution
```

It is built as a **shared harness plus thin per-concern lens files**: `assess.md` defines the common protocol, and each
`lenses/<concern>.md` supplies the concern's focus, lead personas, and rubric. The whole family is exposed as ONE parameterized command,
`/assess <concern>` (e.g. `/assess security`, `/assess prose`).

### The verification / evidence layer (`verify`)

`verify` converts "the agent says the tests pass" into machine-checkable evidence. Its
deterministic helper `verify/tools/run_checks.py` (stdlib-only) DISCOVERS the repo's own test/lint/build/type-check commands, runs approved checks, and records real exit codes, metrics,
and log excerpts as committed evidence. A hard denylist blocks network/deploy/publish/install commands even under `--yes`.

### Versioning and self-tests

The framework uses git-tag-driven semantic versioning (baseline `v1.0.0`; DECISIONS
D44). The version is DERIVED from the git tag by the resolver in `versioning.py` and
baked into `.aw/system/VERSION` (a generated artifact, not hand-edited). A clean tagged checkout resolves to a plain
semver (e.g. `1.0.0`); an ahead-of-release or dirty tree resolves to a PEP 440
`1.0.1.devN+g<sha>` local version.

The Python tools and CLI engines have extensive stdlib-`unittest` self-tests under `tests/`, run canonically with `make test` (parallel `pytest -n auto` after `pip install '.[test]'`, with an automatic serial fallback); `make test-serial` (`python3 -m unittest discover -s tests -t .`) is the guaranteed no-dependency serial runner.

## Invocation, by tool

The workflow *bodies* are tool-agnostic; only the native `/command` convenience is
tool-specific:

1. **OpenCode:** native `/command` from `.opencode/commands/*.md`.
2. **Claude Code:** native `/command` from `.claude/commands/*.md`.
3. **Cursor, Codex, Antigravity, VS Code Copilot, and any other agent:** use the universal fallback: "Read and execute `.aw/system/workflows/<...>`".
4. **Discoverable everywhere:** the `AGENTS.md` pointer leads to `.aw/system/workflows/index.md`, whose "Running a workflow (by tool)" table is the canonical per-tool guide.
