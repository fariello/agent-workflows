# Architecture

How this repository and its main artifact, the `release-review/` framework, are
structured, and why they take this shape. For the dated decision history and the
reasoning behind specific choices, see `DECISIONS.md`. For the values that guide the
work, see `GUIDING_PRINCIPLES.md`.

## What this repository is

`ai-coding` is a collection of resources for AI-assisted software development. Its
centerpiece is `release-review/`, an executable runbook that an AI coding agent
follows to perform a deep pre-release review of *another* repository and leave it
materially better, with a durable, auditable record of what it did and why.

```
ai-coding/
  README.md                 Overview and entry point
  ARCHITECTURE.md           This file
  DECISIONS.md              Dated decision log (the "why")
  GUIDING_PRINCIPLES.md     Values guiding the work
  prompts/                  Reusable prompts (e.g. fix-bar.md, the Fix Bar source)
  release-review/           The framework (canonical source of truth) + its installer
    plan-review.md          Pre-execution plan reviewer (plan-time sibling)
  .opencode/commands/       OpenCode slash-command wrappers (/release-review[-plan], /plan-review)
```

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

Every run creates `repository-review/<RUN_ID>/` (timestamped). This directory - not
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

`install-release-review-to-opencode.py` installs the framework into a target repo by
copying the live `release-review/` directory and the `.opencode/commands/` wrappers
directly from this repo, conservatively (required-files check, safe in-tree paths,
backups, dry-run). There is no committed archive: installing from the source
directory avoids a redundant binary blob and the drift it caused (see `DECISIONS.md`
D12).

It performs a **clean sync** by default: framework files present in the target but no
longer in the source (renamed or removed) are pruned, so the target never accumulates
stale instruction files. Pruning is strictly scoped to the framework namespace
(`release-review/` and the two command wrappers) and never touches
`repository-review/` run records, user code, or anything else. The installer is
git-aware but never commits: installed files are staged with `git add`, pruned
tracked files with `git rm`, untracked files are written/removed on disk, and the
user reviews and commits. `--no-prune` reverts to additive-only. The installer does
not modify `.gitignore`; it only warns if the target repo ignores
`repository-review/`, since run artifacts are committed deliverables.

### Plan review (plan-time sibling)

`release-review/plan-review.md` is a standalone, single-file reviewer for the other
end of the lifecycle: it reviews and improves a proposed implementation plan *before*
any code is written, then `release-review` reviews the finished code before shipping.
Catching a flaw on paper is far cheaper than catching it in code. It deliberately
reuses the shared policy (the Fix Bar in `fix-decision-policy.md` and the eight
personas in `00-run-protocol.md`) rather than redefining them, discovers the project's
own principles/contributor-contract/plan-format/stack/domain-invariants instead of
hardcoding any, and edits planning documents only (never code). It is intentionally a
single prompt, not a modular framework, because plan review is a lighter job (KISS).
It ships with the framework and installs as `/plan-review`.

## Three ways to invoke

1. **OpenCode:** `/release-review` (full) or `/release-review-plan` (audit + plan,
   stop before implementation); `/plan-review` (review a plan before building).
2. **Any agent:** "Read and execute release-review/README.md" (release review) or
   "Read and execute release-review/plan-review.md" (plan review) from the repo root.
