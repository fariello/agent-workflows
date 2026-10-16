<!-- aw-prompt: Kind: run-once | Id: 7z2j3m | Set: testhyg | Status: reusable | Created: 2026-10-16 | Author: opencode (its_direct/pt3-claude-opus-5.5-1m-us) | Targets: AI coding agent | Concerns: Reusable periodic test-suite hygiene: prune non-behavioral and marginal tests, keep the core tier fast and broad, move less critical tests to the thorough tier, consolidate and speed up, without losing regression detection . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a principal test architect doing a PERIODIC test-suite hygiene pass on the `agent-workflows` repository. It is public and is the codebase under discussion: https://github.com/fariello/agent-workflows. This prompt is reused every few weeks, so first find out what changed since the last pass, then keep the suite small, fast, meaningful and trustworthy without weakening its ability to catch regressions.

# Read first (and trust the files over this prompt)

`AGENTS.md` (repo-local "Repository development contract" and the execution contract), `GUIDING_PRINCIPLES.md` P16 ("Test outcomes and behavior, never code structure or text", including its table-driven-test guidance), `CONTRIBUTING.md` (how to run the tiers and the measurement tooling), `pyproject.toml` `[tool.pytest.ini_options]`, the root `conftest.py`, `Makefile`, `.pre-commit-config.yaml`, `.github/workflows/tests.yml`, and `DECISIONS.md` before declaring any path or layout dead.

Find the PREVIOUS hygiene pass: search the records for research with topic `testing` and Sets such as `testhyg`, `testprune`, `testtier` (`aw find research --topic testing`, `aw find plans --set testhyg`). Its final report holds the last baseline numbers, the decision table, and any tests deliberately kept despite matching a delete criterion with a recorded reason. Respect those reasons unless the code they protected has changed.

# Policy this pass enforces (the maintainer's rules)

- **Two tiers.** Bare `pytest` / `python3 -m pytest` runs the CORE tier: tests explicitly marked `core`, broad across every subsystem, finishing in under 30 s wall time (warm median) with 6 xdist workers on the maintainer's 12-CPU host. Everything else runs only in the THOROUGH tier (`make test-all`, `aw suite --thorough` if present), which runs on push (pre-push hook), in CI, and before release. Bare `pytest` never runs the thorough tier. If the repository does not yet implement these tiers as described, STOP after measuring and report the gap instead of improvising a different mechanism.
- **Tests test FUNCTION.** Delete tests that read production source (`inspect`, `ast`, regex or substring over `agent_workflows/**`), pin method or symbol names that are not a documented contract, count callers or lines, pin docstrings or prose in production files, or exist only to block refactoring or architectural change. A name IS a contract when it is a CLI verb or flag, an `aw.agent/v1` field, an exit code, a documented Python API, a front-matter field, or a filename grammar; test those by USING them. Keep a change-restricting test only with a written, compelling reason (for example a security boundary), and convert it to a behavior test where possible.
- **Dependencies are kept SMALL, not zero.** A test asserting a module is "stdlib-only" is a refactoring freeze, not a contract; delete it unless it guards a documented packaging promise (for example a module that must import before dependencies are installed), in which case test that promise by running it.
- **Marginal, duplicate, tautological and obsolete tests go**, except regression tests that cite a backlog id6, plan id6 or incident: those encode a bug that happened, so CONSOLIDATE them, never delete them.
- **Never weaken an assertion to gain speed, never delete a flaky test silently** (fix it, or quarantine it with a backlog item), and keep `aw.agent/v1` conformance, exit-code contracts, leak-sanitizer rules, release and lifecycle gates, and the `livecorpus` tests (thorough tier only).

# How to work (non-negotiable)

- Work ONLY in an isolated git worktree. Never edit, stage or commit in the main checkout. Before a plan exists: `git worktree add .aw/worktrees/<name> -b aw/<name> main`; once approved: `aw work begin <plan-id6>`.
- Measure first, then author a plan Set with `aw ipd scaffold` (Set id `testhygYYMM`, 14 characters or fewer; an orchestrator plus one child per kind of change: tier membership, deletions, consolidation, speed-ups, proof). Make every plan review-ready (`aw ipd lint` conforming, `E-*`/`V-*` with pasted-evidence demands), set them `to-review`, and STOP for human review and approval before deleting or moving anything. Never write `- Readiness:` or `- Approval:` yourself.
- Commit only via `aw commit <plan-id6> -- <paths>`, in small batches per subsystem. Never `git add -A`, never push, never tag. Publish via `aw integration-lock -- git merge --ff-only <branch>`, re-reading `main` inside the lock.
- Paste ACTUAL output as evidence. Repository-relative paths only. Run `aw sanitize --agent` before committing research.

# Step 1: measure (record as research with `aw research new --kind assessment --set <your set> --topic testing`)

1. Counts: `python3 -m pytest --collect-only -q` (core) and `python3 -m pytest tests/ -m '' --collect-only -q` (thorough); per-module test counts; parametrize functions with the most cases.
2. Wall time: three warm runs of each tier (median), `--durations=50` for each.
3. Coverage: line AND branch coverage of `agent_workflows/` per module for core and for thorough, using the repository's own per-test coverage tooling if it exists (look under `tests/tools/` and `CONTRIBUTING.md`). Per-test contexts must be recorded per test id, in-process AND in spawned subprocesses; do NOT trust per-test numbers from plain `--cov-context=test` on Python 3.14, which was measured to miss many tests and every subprocess. Report tests with no unique lines or branches, groups with identical or subset coverage, and modules or `aw` leaf commands (`command_surface.get_declared_leaves()`) that core does not execute.
4. Drift since the last pass: tests added since its baseline commit (`git log --diff-filter=A --name-only <baseline>..HEAD -- tests/`), new `core` markers, new slow tests, new structure pins (re-run the structure-pin scan), and any test over 2 s without a recorded justification.
5. Flakes: three core runs and one thorough run under `pytest-randomly`; record any order-dependent failure.

# Step 2: decide (one table, every module, with a reason per decision)

For each test module: KEEP, MOVE OUT OF CORE (less critical, slow, or redundant within core but useful in thorough), MOVE INTO CORE (cheap and covers a module or leaf core misses), CONSOLIDATE, SPEED UP, or DELETE (name the policy rule above). Optimize core for breadth per second: prefer many small behavioral unit tests and a handful of end-to-end smoke tests; cheapest test that executes each module and each leaf.

# Step 3: plan, stop for approval, then execute

Speed-up techniques to consider: in-process `cli.main([...])` instead of a subprocess where the process boundary is not under test (keep a few true subprocess smoke tests); shared copy-on-write fixtures for temp git repos and installs; seeded small projects instead of this repository's large live records tree; clock injection instead of `sleep`; mocking host-binary and network probes at the boundary; splitting very long tests so `--dist=worksteal` balances.

# Step 4: prove nothing was lost

- Union line and branch coverage of `agent_workflows/` for the thorough tier does not drop; list every line or branch that lost all coverage and restore or justify it.
- Core still executes every module and every leaf it executed before, and stays under 30 s.
- Mutation spot-check: for a random sample (record the seed) of at least 20 deleted, moved or consolidated tests, plus every deleted or consolidated test that cites a defect id, introduce the bug it guarded as a one-line mutation and show that SOME remaining test (in the tier it now lives in) fails; revert and show a clean diff. Any uncaught mutation means restore the test or write a better behavioral one.
- Three randomized core runs and one thorough run pass.

# Deliverable

A final report recorded as research (`aw research new --kind assessment`) AND returned as a single DOWNLOADABLE markdown (`.md`) file containing: before/after counts, tier wall times, `--durations=20`, coverage per tier (line and branch), the decision table with counts per category and every deleted node id with its reason, tests kept despite matching a delete rule and why, mutation results with the seed, flakes and their disposition, and every file changed by path. Close by naming the baseline commit this pass measured, so the next pass can diff from it.
## Workflow history
- 2026-10-16 same-status (aw set): standing periodic test-hygiene prompt
