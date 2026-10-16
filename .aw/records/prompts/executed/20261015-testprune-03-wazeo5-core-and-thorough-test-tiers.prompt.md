<!-- aw-prompt: Kind: run-once | Id: wazeo5 | Set: testprune | Status: executed | Created: 2026-10-15 | Author: opencode (its_direct/pt3-claude-opus-5.5-1m-us) | Targets: AI coding agent | Concerns: Two test tiers: core default under 30s on 6 CPUs, thorough pre-push/release suite (unified from 86tbqk and the opencode draft) . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a senior test-infrastructure engineer working in the `agent-workflows` repository. It is public and is the codebase under discussion: https://github.com/fariello/agent-workflows. Your task is to give it two test tiers: a fast CORE gate that runs by default, and a THOROUGH regression suite that runs before push and before release.

# Read first (do not trust this prompt's summary of them)

`AGENTS.md` (especially the repo-local "Repository development contract" and the execution contract), `GUIDING_PRINCIPLES.md` (P11 deterministic checks, P16 test outcomes not code structure), `CONTRIBUTING.md`, `RELEASING.md`, `pyproject.toml` `[tool.pytest.ini_options]`, the root `conftest.py`, `Makefile`, `.pre-commit-config.yaml`, `.github/workflows/tests.yml`, `agent_workflows/suite_cache.py` (`aw suite`), `.aw/system/workflows/release-review/08-final-ship-review.md`, and the measurement record `.aw/records/research/reference/202610/20261015-pytest-speed-01-sjapfs-pytest-suite-runtime.assessment.md`.

# How to work (non-negotiable)

- Work ONLY in an isolated git worktree. Never edit, stage, or commit in the main checkout. Before a plan exists: `git worktree add .aw/worktrees/<name> -b aw/<name> main`; once a plan is approved: `aw work begin <plan-id6>`.
- First author an Implementation Plan Document (IPD) with `aw ipd scaffold` (Set id `testtier` or similar, 14 characters or fewer), make it review-ready (`aw ipd lint` conforming, real `E-*`/`V-*` items, each `V-*` demanding pasted evidence), set it `to-review`, and STOP for human review and approval. Do NOT write `- Readiness:` or `- Approval:` yourself.
- Commit only via `aw commit <plan-id6> -- <paths>`. Never `git add -A`. Never push or tag. Publish to `main` only via `aw integration-lock -- git merge --ff-only <branch>`, re-reading `main` inside the lock.
- Paste ACTUAL command output as evidence. Never claim a result you did not run. Use repository-relative paths only, never absolute paths or `file://` URLs.

# Current state (verify each claim before relying on it)

- About 8,700 tests in about 510 modules. The full run (`make test-all` = `python3 -m pytest tests/ -m ''`) took about 526 s on 6 workers on the maintainer's 12-CPU Linux host.
- The default is already narrowed: `testpaths` lists 19 hand-picked modules and `addopts` is `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; it ran in about 17 s. Markers `slow` and `livecorpus` exist (read their stated reasons in `pyproject.toml`; `livecorpus` tests are deliberately kept out of runner merge gates).
- `conftest.py` caps xdist at min(6, half the CPUs) and enforces per-test timeouts.
- `.pre-commit-config.yaml` has `default_install_hook_types: [pre-commit, pre-merge-commit]` and no pre-push stage.
- CI (`tests.yml`) runs `python -m pytest tests/ -n auto` across three OSes plus an ADVISORY `-m slow` step with known failures tracked by backlog items.
- `aw suite` runs bare `python3 -m pytest` (`suite_cache.SUITE_CHECK_ARGV`) with a tree-keyed result cache; the runners' merge-and-revalidate gate uses it, so the core tier IS the merge gate for every lane.

# Objective

1. **Tier 1, CORE (the default).** Bare `pytest`, bare `python3 -m pytest`, and `make test`, run from the repository root with no arguments, run the core tier. Requirements:
   - Under **30 s wall time** with 6 xdist workers on the reference host, warm (median of three consecutive runs).
   - Broad regression detection across every subsystem, chosen by MEASUREMENT (below), not by intuition.
   - No `slow` subprocess-heavy integration runs, no full temp-repo installs beyond a few smoke tests, no `livecorpus` sweeps.
2. **Tier 2, THOROUGH.** One command (`make test-all`, optionally also an `aw suite` mode if it fits `suite_cache` cleanly) runs every retained test, including `slow` and `livecorpus`. Bare `pytest` never runs it. It runs at most on push (pre-push hook) and at minimum before release (release-review Section 8 already requires the full target; keep that requirement pointing at this command).

# Requirements

1. **Selection mechanism: explicit, greppable, author-owned.** Replace the hand-curated `testpaths` file list with an explicit `core` marker (module-level `pytestmark` or per-test) and make the default select `-m core` across `tests/`. A new test is NOT core unless its author marks it. Evaluate and reject the alternatives in the plan: keeping a `testpaths` list (whole-file granularity, drifts silently), a `core/` directory split (churns history, forces file moves), `-k` expressions (fragile). If you conclude a different mechanism is better, justify it with the same rigor.
2. **Coverage-driven membership.**
   - Build a map from every first-party module in `agent_workflows/` and every `aw` CLI verb (enumerate from `agent_workflows/command_surface.py` declarations) to at least one core test that EXECUTES it (calls it or drives the CLI) and asserts an outcome.
   - Measure line and branch coverage of `agent_workflows/` with `coverage.py` (already installed; add it to the `test` extra if you depend on it) for the core tier and for the thorough tier. Report both, per module. Target: every module covered by core, and core total coverage within a fraction of thorough coverage that you state and justify. Name each module or verb core cannot cover within budget and why.
   - Prefer many fast behavioral unit tests in core. Keep a SMALL set of true end-to-end smoke tests (one install into a temp repo, one runner `--prepare-only` path, one `aw ipd lint`, one `aw check`, one `aw.agent/v1` record conformance check) because they catch integration breaks unit tests miss.
3. **Budget guard.** Add a cheap, deterministic guard that fails the core run when it exceeds the budget on the reference configuration, printing the slowest tests (`--durations`). It must not flake: measure warm, allow a documented margin, and only warn (not fail) on hosts with fewer than 6 usable CPUs or under CI load. The guard itself must add negligible time.
4. **Pre-push hook.** Add a local hook in `.pre-commit-config.yaml` with `stages: [pre-push]` that runs the thorough tier, and add `pre-push` to `default_install_hook_types` (or document `pre-commit install --hook-type pre-push`). It must reuse the `aw suite` cache so an unchanged tree does not re-run, stream progress, and block the push on failure. State plainly in the docs that it is local feedback, skippable with `--no-verify`, and not an authority boundary; CI and release-review are the authority. Do NOT also ship a hand-written `.git/hooks/pre-push`: one mechanism, consistent with how this repo treats hooks.
5. **CI.** Run the core tier as the required fast job on every OS. Run the thorough tier as a separate job, required where it is green, advisory only for named tests with tracked backlog items (keep the existing tracked-advisory pattern). Fix any comment in `tests.yml` that no longer matches the YAML.
6. **Runner and agent contract.** Keep `aw suite` and the runners' merge gate on the CORE tier, and state that explicitly. Update every place that names test commands so they agree: the repo-local "HOW TO RUN THE SUITE" paragraph in `AGENTS.md` (below the managed block; the managed block itself must stay project-agnostic), `CONTRIBUTING.md`, `RELEASING.md`, `Makefile` comments, `docs/` pages, and release-review Section 8.
7. **No silent loss.** This task must not delete or skip any test: everything not in core still runs in the thorough tier. Prove it with `python3 -m pytest tests/ -m '' --collect-only -q` counts before and after, which must be equal. (Pruning is a separate prompt, `testprune` Order 04; if it lands first, re-baseline.)
8. **Determinism.** Core passes three consecutive runs under `pytest-randomly` ordering with 6 workers, no flakes. Fix any flaky test found, or remove it from core with a recorded reason and a backlog item.
9. **Failure demonstration.** Show that a deliberately introduced regression (one-line mutation in a core-covered module) fails the core tier, and one in a thorough-only path fails the thorough tier and blocks a push. Revert both and show a clean diff.

# Evidence required in the final report

- Core: three warm wall times (median under 30 s), test count, `--durations=20`.
- Thorough: wall time, test count, and equal before/after collect-only counts.
- Per-module coverage table (core vs thorough) and the module-and-verb-to-core-test map.
- Pre-push hook: an unchanged tree hits the cache; a one-line change re-runs; a failure blocks the push.
- The two mutation demonstrations with reverts.
- Every file changed, by path.

Return your final report as a single DOWNLOADABLE markdown (`.md`) file.
## Workflow history
- 2026-10-16 executed (aw set): executed: produced plan hguae9 (to-review) and research 7ry5kv; implementation awaits plan approval
