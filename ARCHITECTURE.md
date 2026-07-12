# Architecture

How this repository and its main artifact, the `release-review/` framework, are
structured, and why they take this shape. For the dated decision history and the
reasoning behind specific choices, see `DECISIONS.md`. For the values that guide the
work, see `GUIDING_PRINCIPLES.md`.

## What this repository is

`agent-workflows` is a collection of resources for AI-assisted software development. Its
centerpiece is a set of reusable **agent workflows** under `.agents/workflows/`. The
flagship, `release-review`, is an executable runbook that an AI coding agent follows
to perform a deep pre-release review of *another* repository and leave it materially
better, with a durable, auditable record of what it did and why.

```
agent-workflows/
  README.md                 Overview and entry point
  ARCHITECTURE.md           This file
  DECISIONS.md              Dated decision log (the "why")
  GUIDING_PRINCIPLES.md     Values guiding the work
  AGENTS.md                 One-line pointer to the workflow index (mirrored into CLAUDE.md/GEMINI.md if they exist)
  install-workflows.py/.sh  Installer (human-run bootstrap; at the root, not a workflow)
  tests/                    Stdlib-unittest self-tests for the Python tools
  .agents/workflows/        Reusable agent workflows (canonical source of truth)
    VERSION                 Framework version (semver, tag-derived); stamped into targets
    index.md                Workflow manifest (installer reads it to generate shims)
    release-review/         The full, all-concerns pre-release review framework
    plan-review/            Pre-execution plan reviewer (plan-time sibling)
    plan-review-long/       Modular multi-file variant of plan-review (parity)
    assess/                 Single-concern assessment harness + per-concern lenses
      assess.md             Shared harness (assess one concern -> IPD, no auto-execute)
      lenses/               One lens per concern (performance, security, ...)
      references/           Shared references (e.g. prose-style.md)
      templates/            IPD, run-report, and findings-CSV templates
      tools/scan_secrets.py Read-only secret/PII scanner (tree + history)
    assess-all/             Cross-concern rollup orchestration
    advise/                 Interrogate-and-coach harness + persona charters
      personas/             One charter per expert persona (skeptic, architect, ...)
    verify/                 Evidence layer (proof, not self-report)
    verify-execution/       Post-execution cross-check that a plan was truly done
      tools/run_checks.py   Discovers and runs the repo's own checks; captures evidence
    benchmark/              Guided performance benchmarking (informational)
      tools/bench_env.py    Read-only machine/environment capture + diagnosis + HPC detect
    setup-repo/             Guided setup + conformance wizard
      tools/setup_tools.py  Deterministic tool-install helper
      tools/normalize_plan_names.py  Check/normalize plan filenames to the convention
    scaffold/               Guided authoring of a new lens/persona/workflow/command
    spec/                   Draft a reviewable specification (front of funnel)
    incident/               Blameless post-mortem (reactive operations)
    release-notes/          Version bump + changelog/notes (release discipline)
    migrate/                Assess-and-plan a high-risk migration
    list-workflows/         Toolkit discovery (capabilities + installed version)
    getting-started/        Guided in-agent tour and router for newcomers
  .agents/docs/             Durable reference docs (research, walkthroughs, specs,
                            prompts, roadmaps)
    prompts/                Historical/reference prompt library (e.g. fix-bar.md, an
                            origin note for the Fix Bar; see its README)
  .opencode/commands/       Generated OpenCode shims (one per command, 18)
  .claude/commands/         Generated Claude Code shims (same set)
```

### Capability layout (open-ended)

Each workflow is a capability with its own subdirectory under `.agents/workflows/`,
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

```
README.md            Controlling instruction + orchestration (per-section loop)
00-run-protocol.md   Global rules: personas, Fix Bar summary, MEM/LIVE rules,
                     durable-knowledge objective, IDs, registers, commit/push, safety
fix-decision-policy.md   Canonical Fix Bar (fix-by-default, Remediation-Risk gate)
reference.md         On-demand look-up material (type codes, ID examples, schema/CI lists)
01-current-state.md          Inventory and discovery
02-quality-security-edge-cases.md   Bugs, security, MEM, LIVE
03-tests-regression.md       Test/regression gaps
04-docs-specs-examples.md    Docs + durable-knowledge audit
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
execution mode (see below).

### State: the authoritative run directory

Every run creates `workflow-artifacts/<workflow-name>/<RUN_ID>/` (timestamped;
`release-review` for the runbook). This directory - not
the chat transcript or TodoWrite - is the authoritative record: metadata, inventory,
finding/action registers (CSV), decisions, commands, commits, checkpoints, the
implementation plan, validation results, push plan, the final report, plus
specialized artifacts (schema validation, TODO reconciliation, guiding-principles
assessment, cold-start orientation, persona review) and `section-summaries/`
per-phase reports.

**Why externalize state to files:** long multi-step LLM runs degrade when state lives
only in context. File-based state makes runs recoverable, auditable, committable, and
enables fresh-context phase isolation. This is the load-bearing architectural
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

### Distribution

`install-workflows.py` (at the repo root; a human-run bootstrap tool, distinct from the
agent-executed workflows) installs the workflows into a target repo by
copying the live `.agents/workflows/` tree directly from this repo, conservatively
(manifest-driven, safe in-tree paths, backups, dry-run). There is no committed
archive: installing from the source directory avoids a redundant binary blob and the
drift it caused (see `DECISIONS.md` D12).

It performs a **clean sync** by default: framework files present in the target that
differ from the source are updated in place (backed up first unless `--no-backup`), and
framework files no longer in the source (renamed or removed) are pruned, so the target
never accumulates stale instruction files and updating is just a re-run (no `--force`;
there is no such flag). This overwrite-by-default posture is the companion to
prune-by-default: if deleting a stale framework file by default is safe with backups,
git staging, and `--dry-run`, overwriting one is strictly safer (see `DECISIONS.md`
D23). Pruning is strictly scoped to the framework namespace
(`.agents/workflows/` plus the generated shim files) and never touches
`workflow-artifacts/` run records, user code, or anything else. The installer is
git-aware but never commits: installed files are staged with `git add`, pruned
tracked files with `git rm`, untracked files are written/removed on disk, and the
user reviews and commits. `--no-prune` reverts to additive-only. The installer makes
one narrow `.gitignore` change: it adds its own local backup dir
(`.agent-workflows-installer-backups/`) so that scratch is never committed. Otherwise
it does not manage `.gitignore`; in particular it only *warns* if the target ignores
`workflow-artifacts/`, since run artifacts are committed deliverables (see
`DECISIONS.md` D24). It also never copies Python build cruft (`__pycache__`, `.pyc`)
into a target.

It also **migrates pre-restructure repos** on install (staged, never committed): it
removes the old root `release-review/` framework directory (the new copy is installed
under `.agents/workflows/`) and `git mv`s old `repository-review/<RUN_ID>/` run records
into `workflow-artifacts/release-review/` so their committed history moves rather than
being lost. The migration is guarded so it never fires on the framework's own repo or
a repo already on the new layout, and reports exactly what it moved/removed.

It also **generates the per-tool slash-command shims** from the `index.md` manifest
(into `.opencode/commands/` and `.claude/commands/`) and adds a one-line **pointer
block** to the target's `AGENTS.md` (and existing `CLAUDE.md`/`GEMINI.md` files). The shims and the pointer are the only
tool-specific surface; the workflow bodies are tool-agnostic. Tools without native
slash commands use the universal fallback: read `.agents/workflows/index.md` and
"read and execute" the workflow body.

### Plan review (plan-time sibling)

`.agents/workflows/plan-review/plan-review.md` is a standalone, single-file reviewer
for the other end of the lifecycle: it reviews and improves a proposed implementation
plan *before* any code is written, then `release-review` reviews the finished code
before shipping. Catching a flaw on paper is far cheaper than catching it in code. It
deliberately reuses the shared policy (the Fix Bar in
`../release-review/fix-decision-policy.md` and the eight personas in
`../release-review/00-run-protocol.md`) rather than redefining them, discovers the
project's own principles/contributor-contract/plan-format/stack/domain-invariants
instead of hardcoding any, and edits planning documents only (never code). It is
intentionally a single prompt, not a modular framework, because plan review is a
lighter job (KISS). It installs as `/plan-review`.

The release-review runbook also ships a **planning-only variant, `release-review-plan`**:
it shares the same body but runs it in planning-only mode - completing the audit and a
consolidated implementation plan, then stopping before implementation. It installs as
`/release-review-plan`.

### Assessment workflows (single-concern, IPD-producing)

`.agents/workflows/assess/` is a family of focused reviewers that sit between
`plan-review` and `release-review` in the pipeline: each assesses ONE concern deeply
and writes a dated Implementation Plan Document (IPD) into the project's pending-plans
directory for human approval, rather than fixing in place or auto-executing:

```
/assess <concern>  ->  IPD in pending/  ->  plan-review (optional)  ->  approval  ->  execution
```

It is built as a **shared harness plus thin per-concern lens files**, not 20 separate
prompts: `assess.md` defines the common protocol (discover conventions, eight personas,
Fix Bar applied as "what to propose", write an IPD, never execute), and each
`lenses/<concern>.md` supplies the concern's focus, lead personas, and rubric. This
keeps the protocol single-sourced and makes adding a concern cheap: a new lens file
plus a manifest row. The whole family is exposed as ONE parameterized command,
`/assess <concern>` (e.g. `/assess security`, `/assess prose`), not one command per
concern: the `assess-<concern>` manifest rows are the concern CATALOG (the source of
truth for each concern's lens and for the picker) and do not each generate a shim; the
single `assess` row generates the command, which resolves its first argument to a lens
(DECISIONS D31). A bare `/assess` lists the concerns and asks. `compliance-readiness` is
a single parameterized lens that takes the regime, rather than one workflow per
regulation. The harness reuses the Fix Bar and personas from `../release-review/` as a
sibling. Choose `/assess <concern>` to investigate one concern and propose a plan;
`release-review` for a broad review that fixes in place; `assess-all` (below) to run the
family and get one prioritized, cross-concern plan.

The family includes cybersecurity lenses (`data-exfiltration`, `intrusion-detection`,
`ransomware-resilience`, `threat-model`, `logging-audit`, `secrets`) and a
`compliance-readiness` lens parameterized by regime (FIPS, NIST 800-171, CMMC L2).
The `secrets` lens (and a mandatory step in `release-review`) runs a deterministic,
read-only, redacting scanner - `assess/tools/scan_secrets.py` - over the working tree
AND git history to find committed secrets/keys and PII/PHI without relying on the LLM
to crawl millions of lines; it recommends installing a mature scanner
(gitleaks/trufflehog/detect-secrets) and merges their results if present, and the
proposed remediation is rotate-first, then purge-history, then prevent (DECISIONS D23).
Because those regimes are mostly organizational rather than code, the
compliance-readiness lens is deliberately constrained: it assesses only the
repo-visible technical slice, classifies every control as repo-verifiable vs.
org-level-out-of-scope, never emits an overall "compliant" verdict, and states it is
not a certification or a substitute for a qualified assessor. This honest repo-vs-org
split is a design requirement, not a limitation to paper over (DECISIONS D20).

The family also includes `generalization` (productization): reuse across
organizations, tenants, and deployments; configuration architecture; admin/operability;
and de-hardcoding org-specific assumptions. It is the reuse-focused sibling of the
`architecture` lens (structural soundness) and defers to `security` for authz/secrets
(DECISIONS D22).

`prose` assesses the *writing style* of all prose in the repo (docs, comments/
docstrings, UI strings, error/help text, commit messages) against a framework-owned,
distilled nonfiction style guide (`assess/references/prose-style.md`, adapted from the
maintainer's nonfiction-prose toolkit): quiet force, no mechanical fingerprints,
modifier restraint, no em dashes, applied at surface-appropriate intensity. It is the
style sibling of `documentation` (accuracy/completeness) and `self-documentation`
(in-product learnability), and is the one assess lens with an optional author-in-the-
loop interactive edit mode, because prose edits are voice-bearing (DECISIONS D28).

`assess-all` is the cross-concern rollup: it runs the family (all, a group, or a
subset - confirming scope and cost first), then synthesizes ONE prioritized,
de-duplicated IPD plus a rollup record, rather than N disconnected IPDs. It orchestrates
the existing lenses (which stay the single source of truth) and adds the synthesis and
cross-prioritization layer; it is the broad propose-a-plan review, the companion to
`release-review`'s broad fix-in-place review. Its command gets its own shim despite the
`assess-` prefix, via a documented installer exception (DECISIONS D36).

### The verification / evidence layer (`verify`)

`verify` converts "the agent says the tests pass" into machine-checkable evidence. Its
deterministic helper `verify/tools/run_checks.py` (stdlib-only, like `scan_secrets.py`)
DISCOVERS the repo's own test/lint/build/type-check commands (from `package.json`,
`Makefile`, `pyproject`/`tox`, `justfile`, CI files), runs the ones the user approves
(confirm-per-check by default, `--yes` for batch), and records real exit codes, metrics,
and log excerpts as committed evidence. A hard denylist blocks network/deploy/publish/
install commands even under `--yes`, and it is honest about what it could not run (a
partial run never reads as a full green). `release-review` and the `assess` testing lens
cite this evidence instead of self-reporting (DECISIONS D33).

### The benchmarking workflow (`benchmark`)

`benchmark` helps a repo gather performance information. It is deliberately
**informational, not a regression gate** (perf numbers are noisy and environment-bound;
gating a build on them by default would be dishonest), with an opt-in baseline-comparison
mode for users who explicitly want a guardrail (DECISIONS D41). Like `verify` and
`setup-repo`, it is a body + a deterministic stdlib helper:

- `benchmark/benchmark.md` is the guided wizard: it authors an ISOLATED benchmark suite in
  the TARGET repo's `benchmarks/` dir, captures and diagnoses the environment, runs the
  suite with warm-up, optionally submits to an HPC scheduler, and produces a shareable
  results bundle - all with per-step consent, staging not committing, never publishing.
- `benchmark/tools/bench_env.py` (stdlib-only, read-only w.r.t. system state, like
  `scan_secrets.py`/`run_checks.py`) does the mechanical parts: DEEP host capture (hostname,
  OS/kernel/arch, CPU model/cores/governor/NUMA/SIMD flags, RAM total/free/available/
  cached/used + swap, load, GPU via nvidia-smi/rocm-smi, per-path filesystem type + free
  space, container/VM hints), CONFIG DIAGNOSIS with copy-pasteable remedies (working set on
  NFS/Lustre/GPFS, powersave governor, swapping, busy host, login-node HPC use,
  virtualization), HPC SCHEDULER detection (Slurm/PBS/SGE/LSF), a bounded disk-speed probe,
  and a cache warm-up pass. It captures rich detail on Linux and degrades honestly
  elsewhere (unknown fields reported, never fabricated).

Four design constraints shape it:

- **Isolation over instrumentation (the "0% impact on the project" requirement).** The
  benchmark suite lives in a separate `benchmarks/` dir that ships no import into the
  product and adds no runtime cost when unused, so *including* it is inert. Timing is done
  out of process (invoke the CLI / entry point) rather than instrumenting the product
  in-process. The docs are honest that *observation* still has some cost; the 0% guarantee
  is about inclusion, not measurement.
- **Read-only on system state.** The tool reads `/proc`, `/sys`, and read-only CLIs and
  only SUGGESTS system changes (governor, mounts) as text; it never applies them.
- **Warm-up and repeatability.** Benchmarks run at least two full iterations so the cold
  first iteration (file-system cache, NFS automount/fetch, JIT/import startup) can be seen
  and excluded from the summary statistic; the tool's `--warm` pre-reads inputs and the
  diagnosis steers NFS working sets to node-local scratch.
- **HPC safety.** Detecting a scheduler leads to generating a submission script and, only on
  explicit PER-SUBMISSION consent, running `sbatch`/`qsub`/`bsub`. Never auto-submitted
  under a batch flag (the same safety posture as `verify`'s denylist).

Sharing is offline by design: the tool makes no network calls and can `--scrub`
hostname/user/paths so a results bundle can be shared without leaking identity.

### The advise persona family (`advise`)

`advise` is a different MODE from review/assess: an interactive interrogate-and-coach
session. It mirrors the assess architecture (one harness + a library of persona
charters under `advise/personas/`), exposed as one parameterized command
`/advise <persona>` (skeptic, spec-editor, architect, red-teamer, staff-engineer,
domain-expert, naive-user). The `advise-<persona>` manifest rows are the persona catalog
(same collapse as `assess-<concern>`); a bare `/advise` lists personas and asks. It
coaches and may edit planning/prose artifacts with per-change consent, but never runs
code (DECISIONS D34).

### Lifecycle workflows (`spec`, `incident`, `release-notes`, `migrate`)

These fill the delivery stages beyond assess/review - discover, ship, operate, and
high-risk change - as distinct guided workflows (DECISIONS D35):

- `spec` turns a fuzzy request into a reviewable specification (goals, non-goals, users,
  testable acceptance criteria); it produces the artifact that `/advise spec-editor`
  interrogates and `plan-review` reviews.
- `incident` runs a blameless, repo-scoped post-mortem and emits follow-up action IPDs;
  it is honest that the operator holds the real monitoring/on-call data.
- `release-notes` decides the version bump from the actual changes and drafts the
  changelog and human notes; it prepares a release but never publishes, tags, or pushes
  (`release-review` Section 9 references it).
- `migrate` assess-and-plans a high-risk migration (framework/DB/dependency/layout) as a
  staged, reversible plan with characterization tests and per-stage rollback + `verify`
  checks, emitted as an IPD.

### Discovery and onboarding (`list-workflows`, `getting-started`)

`list-workflows` is toolkit discovery: it reads the manifest (single source of truth)
and reports the capabilities - core workflows, the `/assess` concerns, the `/advise`
personas - plus the installed framework version, grouped and with per-tool run
instructions (DECISIONS D32). `getting-started` is the newcomer's guided entry point: it
detects repo/toolkit context, explains the mental model briefly, asks the user's goal,
and routes to the right workflow (offering to run it, with consent) with the exact
invocation for their tool. It orients and routes - read-only by default - and references
`list-workflows` for the full catalog rather than duplicating it (DECISIONS D37).

### Versioning and self-tests

The framework uses git-tag-driven semantic versioning (baseline `v1.0.0`; DECISIONS
D44). The version is DERIVED from the git tag by the resolver in `versioning.py` and
baked into `.agents/workflows/VERSION` (a generated artifact - regenerate with
`make version-file`, do not hand-edit). A clean tagged checkout resolves to a plain
semver (e.g. `1.0.0`); an ahead-of-release or dirty tree resolves to a PEP 440
`1.0.1.devN+g<sha>[.dYYYYMMDD]` local version, so a checkout that differs from a release
can never silently report a clean version. The tools stay "dumb" - once copied into a
target they have no git, so they read the neighboring `VERSION` file (three directories
up from each tool); only the resolver knows about git. The value is surfaced in
`index.md` and reported by `install-workflows.py --version` and the tools' `--version`.
The installer stamps `VERSION` into every target (the copied `VERSION` file IS the
installed-version record), so `list-workflows` and `setup-repo` can report which version
a repo has (DECISIONS D32). The five Python tools
(`scan_secrets.py`, `setup_tools.py`, `run_checks.py`, `bench_env.py`,
`normalize_plan_names.py`) plus the installer/CLI (`agent_workflows/`) have
stdlib-`unittest` self-tests under `tests/`, run with `python3 -m unittest discover -s
tests -t .`, covering the installer (fresh install, idempotent re-run, prune, legacy
migration, dry-run, the catalog-row collapse), the scanner (planted secret in tree and
history, redaction, skip-scope), the check runner (classification, the safety denylist,
honest pass/fail), the env tool (each environment diagnosis, HPC detection, scrub, bounded
probe), setup_tools (`--version`, tool table), the plan-filename normalizer
(`normalize_plan_names.py`: parse/legacy-shape/earliest-evidence time/scan/apply/exclusions),
the PyPI long-description link rewriter (`pypi_links.py`: relative -> absolute tag-pinned
GitHub URLs, applied at build time by a hatchling metadata hook so PyPI links resolve while
the source README keeps GitHub-relative links; DECISIONS D58),
and the CLI/config/discovery/packaging. This is the framework holding itself to its own
testing/verification bar (DECISIONS D36).

### Meta / authoring workflows (`setup-repo`, `scaffold`)

Two guided, wizard-style workflows differ in kind from the reviewers: they are
interactive and MAY change files (with per-step confirmation), rather than only
proposing (DECISIONS D24). `setup-repo` walks a repo owner through best-practices and
security setup - detecting state, then ask-before-each-change to install tools (via the
deterministic helper `setup-repo/tools/setup_tools.py`, which detects and, only on
request, installs gitleaks/pre-commit/detect-secrets via the platform's own package
manager) and to add secret-scanning CI + a local hook, `.gitignore` hygiene, hygiene
files, a stack CI baseline, a pre-commit config, dependency hygiene, and (advisory-only)
branch-protection guidance. It is idempotent and stages changes without committing.
`scaffold` walks the owner through adding a new `assess-<concern>` lens, `advise-<persona>`
charter, standalone workflow, or command, then wires the manifest and regenerates shims -
the guided version of the
"add a subdir + a manifest row" extension path. Both are agent-driven conversational
wizards (fitting the agent-executed model), not standalone TUIs; the only scripted piece
is the mechanical tool-install helper the setup wizard calls.

## Invocation, by tool

The workflow *bodies* are tool-agnostic; only the native `/command` convenience is
tool-specific, and support varies (verified against current docs):

1. **OpenCode:** native `/command` from `.opencode/commands/*.md` (frontmatter uses
   `agent:`). E.g. `/release-review`, `/assess security`, `/setup-repo`.
2. **Claude Code:** native `/command` from `.claude/commands/*.md` (still supported;
   its frontmatter uses `description`/`argument-hint`, not `agent:`, so the installer
   generates a tailored variant there). Claude Code's newer *skills* form
   (`.claude/skills/<name>/SKILL.md`) is recommended by Anthropic but we ship the
   still-supported commands form.
3. **Cursor, Codex, Antigravity, VS Code Copilot, and any other agent:** there is **no
   repo-file slash-command mechanism**, so these use the **universal fallback** - "Read
   and execute `.agents/workflows/<...>`". This is the lowest-common-denominator path
   and works everywhere.
4. **Discoverable everywhere:** the `AGENTS.md` pointer leads to
   `.agents/workflows/index.md`, whose "Running a workflow (by tool)" table is the
   canonical per-tool guide.

The installer generates the per-tool shims from the manifest, tailoring frontmatter to
each tool (DECISIONS D25).
