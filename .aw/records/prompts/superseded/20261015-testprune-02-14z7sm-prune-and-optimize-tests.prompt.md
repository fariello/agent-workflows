<!-- aw-prompt: Kind: run-once | Id: 14z7sm | Set: testprune | Status: superseded | Created: 2026-10-15 | Author: Antigravity (gemini) | Targets: AI coding agent | Concerns: Optimize, consolidate, and eliminate marginally useful or non-functional tests . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a Principal Software Engineer and Test Architect specializing in test suite performance optimization, dead code elimination, and high-signal quality engineering in large Python codebases. Your task is to audit, prune, consolidate, and optimize the test suite for the `agent-workflows` repository to reduce total test execution time to under 2 minutes (on 6 CPUs with `pytest-xdist`) while strictly preserving functional regression detection.

# Context and Problem Statement

The repository's test suite currently contains over 8,700 tests across dozens of test files in `tests/`, taking nearly 9 to 10 minutes to run in full. A substantial portion of these tests provides marginal or negative value:
- Brittle tests inspecting internal code structure rather than observable behavior.
- Tests asserting on internal method names, private helper signatures, or symbol counts that act as anti-refactoring barriers.
- Massive combinatorial parameter matrices that test hundreds of nearly identical permutations without testing distinct failure modes or boundary conditions.
- Repetitive, expensive disk operations (e.g. repeated `git init` and subprocess spawning in every test case) that could be consolidated or fixture-shared.
- Low-value tests asserting trivial language or dataclass semantics.

You must design and execute a disciplined pruning, consolidation, and optimization campaign in an isolated worktree to achieve a streamlined, high-signal test suite that executes in under 2 minutes without sacrificing real defect detection.

# Guiding Principles and Pruning Criteria

1. **Test Observable Outcomes, Not Code Structure (Zero Code-Pinning)**:
   - **ELIMINATE IMMEDIATELY**: Any test that reads production source code using `inspect`, `ast`, regex, line counting, or substring search.
   - **ELIMINATE**: Tests asserting on caller counts, symbol censuses, or module line counts as a proxy for correctness.
   - **ELIMINATE**: Tests asserting that specific comments, docstrings, or module banners remain unchanged.
   - **ELIMINATE**: Tests checking internal or private method names (unless the method is an explicit public API contract required by external consumers).
   - **ELIMINATE**: Architectural "purity" tests or anti-change restrictions that artificially restrict development and refactoring without a compelling functional necessity.
   - **PRESERVE**: Tests executing code paths and asserting on observable outputs, exit codes, state mutations, exceptions, and side effects.

2. **Prune Marginally Useful Tests**:
   - **ELIMINATE**: Tests verifying trivial Python mechanics (e.g., testing that assigning an attribute to a dataclass stores the attribute, or asserting `assert result is not None` with no behavioral assertions).
   - **ELIMINATE**: Redundant duplicate tests where multiple test functions assert identical invariant properties through slightly different private helpers.

3. **Consolidate Combinatorial Matrices**:
   - **CONSOLIDATE**: Large `@pytest.mark.parametrize` matrices that generate hundreds of test cases for trivial input variations.
   - **REPLACE**: Retain a focused, representative subset: the happy path, representative boundary values, equivalence partitions, and distinct error/edge conditions.

4. **Optimize Execution Bottlenecks**:
   - Identify tests with slow setup/teardown overhead using `pytest --durations=50`.
   - Where tests repeatedly create temporary git repositories, run git commands in subprocesses, or write large directory trees, optimize them to use shared fixtures, in-memory structures, or direct Python API calls where appropriate.
   - Ensure tests remain isolated, hermetic, and safe for parallel execution with `pytest-xdist`.

5. **Target Performance Threshold**:
   - Running the entire retained test suite (`pytest tests/`) must complete in **under 2 minutes** on 6 CPUs with `pytest-xdist` parallel execution (`-n auto`).

# Execution Plan and Tasks

1. **Test Suite Audit & Profiling**:
   - Run `pytest --durations=100` and identify the slowest test files, classes, and individual tests.
   - Scan `tests/` for code-pinning patterns (`inspect`, `ast`, `re.search` on source files, line/symbol censuses, docstring checks).
   - Catalog test files with disproportionately high test counts or bloated parameterizations.

2. **Categorized Pruning & Removal**:
   - Generate a detailed inventory of tests and test files to delete or prune, categorized by justification (code-pinning, redundant matrix, low utility, trivial assertion).
   - Safely remove non-functional and code-pinning test files and methods.

3. **Parametrization Consolidation**:
   - Refactor bloated parameter matrices in retained test files down to high-signal boundary and representative cases.
   - Verify that all core behaviors, edge conditions, and error branches remain thoroughly tested.

4. **Bottleneck Refactoring**:
   - Refactor identified slow tests and fixtures to eliminate unnecessary subprocess spawning or filesystem thrashing.

5. **Benchmarking and Regression Verification**:
   - Run the updated test suite using parallel execution.
   - Measure and record the exact runtime (`time python3 -m pytest tests/`).
   - Confirm that all retained tests pass cleanly and that total execution time is under 2 minutes.
   - Verify that legitimate functional regressions in key subsystems (CLI commands, state machines, specs, IPD lifecycle, attention views, leak sanitizer) continue to be caught accurately.

# Deliverable Format

Return your complete analysis, audit findings, pruning decisions, code diffs, and benchmark measurements as a single **DOWNLOADABLE markdown (`.md`) file**. Include all exact terminal commands, timing outputs, and git status summaries required to verify and apply the work.
## Workflow history
- 2026-10-16 superseded (aw set): superseded by unified prompts wazeo5 (tiers) and 4ul37x (pruning), merged with the opencode drafts
