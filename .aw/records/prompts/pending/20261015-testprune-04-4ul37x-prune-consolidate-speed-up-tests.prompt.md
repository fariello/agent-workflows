<!-- aw-prompt: Kind: run-once | Id: 4ul37x | Set: testprune | Status: pending | Created: 2026-10-15 | Author: opencode (its_direct/pt3-claude-opus-5.5-1m-us) | Targets: AI coding agent | Concerns: Prune, consolidate and speed up tests to a full retained suite under 2 minutes without losing regression detection (unified from 14z7sm and the opencode draft) . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a principal test architect working in the `agent-workflows` repository. It is public and is the codebase under discussion: https://github.com/fariello/agent-workflows. Your task is to prune, consolidate, and speed up its test suite so the FULL retained suite runs in **under 2 minutes** on 6 xdist workers, while the suite still catches at least every regression it catches today.

# Read first (do not trust this prompt's summary of them)

`AGENTS.md` (repo-local development contract and execution contract), `GUIDING_PRINCIPLES.md` (P16 "Test outcomes and behavior, never code structure or text" is the governing rule, including its "Tabulated and table-driven tests" guidance), `CONTRIBUTING.md`, `DECISIONS.md` (before declaring any layout or path dead), `pyproject.toml`, the root `conftest.py`, and `.aw/records/research/reference/202610/20261015-pytest-speed-01-sjapfs-pytest-suite-runtime.assessment.md`. If the two-tier task (`testprune` Order 03) has landed, read its plan and respect its `core` marker: deleting or weakening a core test needs the same justification as any other and must not open a coverage gap in core.

# How to work (non-negotiable)

- Work ONLY in an isolated git worktree. Never edit, stage, or commit in the main checkout. Before a plan exists: `git worktree add .aw/worktrees/<name> -b aw/<name> main`; once approved: `aw work begin <plan-id6>`.
- First author a plan with `aw ipd scaffold`: an orchestrator plus one child per subsystem (Set id `testprune` or shorter), so each child is one focused, reviewable pass. Make every plan review-ready (`aw ipd lint` conforming), set it `to-review`, and STOP for human review and approval before deleting anything. Do NOT write `- Readiness:` or `- Approval:`. If Order 03 is not executed yet, add an `- Item-Dependencies:` edge on it, or coordinate explicitly, so the two do not rewrite `pyproject.toml`/`conftest.py` concurrently.
- Commit via `aw commit <plan-id6> -- <paths>` in small batches grouped by subsystem. Never `git add -A`, never push, never tag. Publish only via `aw integration-lock -- git merge --ff-only <branch>`.
- Paste ACTUAL output as evidence. Use repository-relative paths only.

# Current state (verify)

About 8,700 tests in about 510 modules; full run (`python3 -m pytest tests/ -m ''`) about 526 s on 6 workers on the maintainer's 12-CPU Linux host; xdist capped at min(6, half the CPUs) by `conftest.py`, `--dist=worksteal`, `pytest-randomly` enabled. A previous pass (commit `ad9213cc6`) already deleted some structure-pinning test files; do not assume that pass was complete.

# What to ELIMINATE (record a one-line reason per deletion)

1. **Code-structure pins (P16).** Tests that read production source (`inspect.getsource`, `ast.parse`, `read_text()` / regex / substring over `agent_workflows/**`), assert which module defines a symbol, count callers or definitions, assert line counts, or pin docstrings, comments, banners, or exact prose in production files.
2. **Name and shape pins**, UNLESS the name is part of an explicit, documented contract that is effectively FUNCTION: a CLI verb or flag, an `aw.agent/v1` record field, an exit code, a documented Python API, a front-matter field, a filename grammar. For a borderline case, test the contract by USING it (invoke the verb, parse the record), then delete the pin.
3. **Architecture and change freezes.** Tests whose only effect is to stop refactoring (forbidden imports between modules, frozen module layout, "stays private", file-size guards). Keep one only with a written, compelling reason that development MUST be restricted (for example a security boundary such as "the sandboxed runner never reaches the network"), and then test the boundary's BEHAVIOR where possible.
4. **Tautologies and mock-only tests.** Tests asserting a mock returns what it was told to, re-implementing the function under test, asserting only `is not None` or no exception where none can occur, or asserting trivial language or dataclass mechanics.
5. **Duplicates.** Tests exercising the same code path with equivalent inputs and assertions as another test, identified by measurement (see Method), not by name similarity.
6. **Marginal tests.** Tests covering no line or branch that others do not AND guarding no recorded defect. Tests citing a backlog id6, plan id6, or incident encode a bug that really happened: CONSOLIDATE them, do not delete them.
7. **Obsolete tests** for removed code paths or permanently disabled flags. The legacy `.agents/` layout is still supported; check `DECISIONS.md` and specs before calling anything dead.

# What to CONSOLIDATE

- Near-identical tests differing only in input become one table-driven test (`pytest.mark.parametrize`, or the accumulate-vs-subTest pattern in P16), with readable case ids.
- Large combinatorial matrices that test hundreds of near-identical permutations are reduced to the happy path, boundary values, one representative per equivalence class, and every distinct error branch. Prove with branch coverage that no branch is lost.
- Tests rebuilding the same expensive fixture (temp git repo, full install, runner state) share a fixture of the right scope, built once and copied per test (`shutil.copytree`) where isolation requires it.
- Several subprocess end-to-end tests differing in one flag become one run asserting several outcomes, or in-process calls (`agent_workflows.cli.main([...])`) where the subprocess boundary is not what is under test.

# What to SPEED UP

- Replace subprocess `aw ...` invocations with in-process calls where the boundary is not under test; keep a small set of true subprocess smoke tests.
- Remove real `sleep`s and wall-clock waits by injecting clocks or shortening timeouts through existing parameters.
- Avoid repeated `git init`, installs, and pip work per test (cached fixtures above).
- Mock host-binary and network probes at the boundary in tests that are not about the host.
- Split or speed up single very long tests so `--dist=worksteal` can balance; after the work, every test over 2 s needs a recorded justification.
- Never weaken an assertion to gain speed.

# Keep, regardless of speed

`aw.agent/v1` conformance, exit-code contracts, leak-sanitizer rules, release gates, lifecycle and status-transition gates, and the `livecorpus` tests (they caught a real parser bug; they stay in the thorough tier). Consolidate these only without loss.

# Method (required, measurable)

1. **Baseline** in the plan: full-suite collect count, three warm wall times (median), `--durations=50`, and per-test coverage contexts (`coverage run --context=test` or `pytest-cov --cov-context=test`) giving each test's line and branch set over `agent_workflows/`.
2. **Classify every test module** as keep / consolidate / speed-up / delete with a reason, in a table recorded as research (`aw research new`). Find duplicates (identical or subset coverage plus equivalent assertions) and marginal tests (no unique lines or branches) from the coverage contexts.
3. **Mutation spot-check.** For a random sample of at least 20 deleted or consolidated tests (and every deleted test that cites a defect id), reintroduce the bug it was meant to catch as a one-line mutation of the code it targeted and show that SOME remaining test fails. Use `mutmut` or hand mutations; paste results. Any mutation nothing catches means: restore the test, or write a better behavioral one.
4. **Flakes.** Any test that fails under `pytest-randomly` reordering or `-n 6` but passes serially is fixed, or quarantined with a backlog item; never silently deleted.
5. **After**: repeat the baseline measurements. Union line and branch coverage of `agent_workflows/` must not drop; list and justify (or restore) every line or branch that lost all coverage.

# Evidence required in the final report

- Before/after: test count, module count, full-suite median wall time (target under 120 s), `--durations=20`, union line and branch coverage.
- Classification counts per category, plus every deleted test's node id and reason.
- Mutation spot-check results.
- Every test kept despite matching a delete criterion, with the compelling reason.
- Flaky tests found and their disposition.
- Every file changed, by path.

Return your final report as a single DOWNLOADABLE markdown (`.md`) file.
