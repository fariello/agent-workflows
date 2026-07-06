# 01 Repository inventory

## Current state summary

`agent-workflows` is a collection of reusable, installable agent workflows for AI coding
assistants. It is a mature, docs-and-instruction-heavy framework plus four small stdlib-only
Python tools and a human-run installer. 182 tracked files. Clean working tree at head a7cf5c3.
Framework VERSION 20260704-05. No product runtime service; the "product" is instruction
files (workflow bodies) + the installer + the tools, consumed by an AI agent.

## Project type and scope

- Type: developer tooling / AI-agent workflow framework (instruction files + Python helpers +
  installer + generated slash-command shims). Tool-agnostic bodies; per-tool shims for OpenCode
  and Claude Code; universal read-and-execute fallback for other agents.
- Scope: install into any repo; run deep pre-release review, plan review, single-concern
  assessments, guided setup, verification, benchmarking, lifecycle workflows, and coaching.

## Intended outcome / audience

- Intent (from README/ARCHITECTURE/DECISIONS): give an AI coding agent a disciplined, honest,
  reusable set of workflows that leave a target repo materially better with an auditable record.
- Audience: developers using AI coding agents; repo owners; maintainers; (self) the framework's
  own maintainer. Stakeholder = the maintainer/community relying on the toolkit's correctness
  and honesty.

## Guiding principles

- Location: `GUIDING_PRINCIPLES.md` (10 principles). Binding contract for this review.
- Summary: P1 fix-by-default/justify-deferral; P2 honest-not-aspirational docs; P3
  self-documenting/learn-as-you-go; P4 durable cold-start knowledge; P5 externalize state;
  P6 KISS/guard scope creep; P7 solve-general-case/project-agnostic; P8 single-source-of-truth;
  P9 design-for-the-model-that-runs-it; P10 safety/reversibility.

## Backlog / TODO sources

- No `TODO.md`/`BACKLOG.md`/`ROADMAP.md`/`KNOWN_ISSUES.md`/`CHANGELOG.md` files.
- Zero real code `TODO`/`FIXME`/`HACK`/`XXX` markers in the Python tools (`git grep` = 0).
- The ~70 "TODO/FIXME" string hits are all instruction TEXT inside workflow bodies (e.g. "TODO.md
  reconciliation" steps), not backlog items. Not a backlog.
- Changelog: DECISIONS.md doubles as the dated, append-only changelog (documented in README).

## Pending agent plans and staged prompts (for Section 8 warning)

- `.agents/plans/pending/`: EMPTY (no pending IPDs).
- `.agents/plans/done/`: 15 IPDs, ALL marked `Status: EXECUTED` (verified each Status line). No
  status/location mismatch (no done plan still says pending).
- `prompts/`: 5 files (README.md + 4 reference prompts). These are a documented historical/origin
  prompt library (prompts/README.md), NOT queued-for-execution staged prompts. Not pending work.
- CONCLUSION: no pending plans or staged prompts. Section 8 pending-plans gate should report
  "none" (clean on this axis).

## Public contract summary

- The installer CLI (`install-workflows.py`): flags `--source/--repo/--dry-run/--no-backup/
  --no-prune/--version`. Human-facing contract.
- The four tools' CLIs: `scan_secrets.py`, `run_checks.py`, `setup_tools.py`, `bench_env.py` -
  each with `--format`/`--version` (except setup_tools, which predates `--version`; see S6).
- The workflow command surface: 16 generated shims (13 core + `assess` + `advise` + `assess-all`);
  `assess-<concern>`/`advise-<persona>` are catalog rows collapsed into the two parameterized
  commands (D31/D34). The manifest `index.md` is the single source of truth.
- VERSION scheme `YYYYMMDD-NN`.

## Artifact / structure summary (in scope: framework is the subject)

- `.agents/workflows/`: 15 workflow capabilities + index.md + VERSION. 29 assess lenses, 7 advise
  personas, 4 tools.
- Root: `install-workflows.py`/`.sh`, README, ARCHITECTURE, DECISIONS (D1-D42), GUIDING_PRINCIPLES,
  CONTRIBUTING, AGENTS, LICENSE (Apache 2.0), NOTICE, CITATION.cff, .gitignore, .gitleaksignore.
- `tests/`: support.py + 4 test files (installer, scan_secrets, run_checks, bench_env).
- `.opencode/commands/`, `.claude/commands/`: 16 shims each (generated).
- `prompts/`: reference prompt library.

## Test and validation inventory

- Self-tests: `python3 -m unittest discover -s tests -t .` => 46 tests, ALL PASS (run this session).
- Installer dry-run on self: NO drift (nothing to install/update/prune) => manifest and generated
  shims are perfectly in sync. Strong internal-consistency evidence.
- CI: `.github/workflows/secret-scan.yml` (gitleaks). (Full CI assessment in Section 6.)

## Version consistency

- `.agents/workflows/VERSION` = `20260704-05`; `install-workflows.py --version` = `20260704-05`;
  `index.md` stamp = `20260704-05`. Consistent across all three surfaces.

## Recent changes (git log context)

- D38 installer fixes; D39 release-review pending-plans warning; D40 scanner nag fix; D41
  benchmark workflow; D42 accessibility terminal rubric. Recent work is the benchmark workflow
  and the accessibility lens (both authored this session, not yet rolled to downstream repos).

## Drift / ambiguities / concerns (seed IDs; detailed in later sections)

- Q1: `setup_tools.py` lacks `--version` while the other three tools have it (consistency; S6).
- Q2: downstream 27 repos are on 20260704-03; source is 20260704-05 (benchmark + a11y not rolled
  out). This is a deliberate, user-gated state, not a defect - note only.
- Detailed correctness/docs/test findings deferred to Sections 2-6.

## Recommended next actions

- Proceed to Section 2 (quality/security/edge-cases) focusing on the four Python tools, since the
  bodies are instruction prose (reviewed for accuracy/consistency in Section 4, not unit-tested).
