<!-- aw-prompt: Kind: run-once | Id: 86tbqk | Set: testprune | Status: superseded | Created: 2026-10-15 | Author: Antigravity (gemini) | Targets: AI coding agent | Concerns: Create under 30s routine test gate and pre-push extended regression suite . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a Senior Test Infrastructure and Systems Engineer specializing in Python developer tooling and high-performance test architecture. Your task is to design, implement, and verify a two-tiered testing workflow for the `agent-workflows` repository that cleanly separates fast, routine developer testing from extended pre-push/release verification.

# Objective and Requirements

The test suite in this repository currently contains over 8,500 tests. Running the entire suite takes 8 to 10 minutes, creating significant friction during daily development, interactive workflows, and automated agent turns. You must establish a reliable mechanism with two distinct tiers:

1. **Tier 1: Core Routine Gate (Default `pytest` / `python3 -m pytest` / `make test`)**
   - Must run in **under 30 seconds** on 6 CPUs on this system using `pytest-xdist` parallel execution (`-n auto`).
   - Must be the automatic default when a developer or agent runs bare `pytest`, `python3 -m pytest`, or `make test` without needing special CLI flags or extra arguments.
   - Must broadly and effectively detect regression bugs by selecting high-signal behavioral tests across all critical subsystems: CLI commands, argument parsing, lifecycle transitions, schema validation, contract checks, attention tracking, runner policies, and leak sanitization.
   - Must exclude slow subprocess integration runs, heavy temp-repo installations, and live-corpus artifact sweeps from this default path.

2. **Tier 2: Extended Pre-Push & Release Regression Gate**
   - Must execute all retained behavioral tests across the repository.
   - Must NOT run automatically during routine `pytest` invocations.
   - Must be configured to run before pushing code to the remote repository (via a git `pre-push` hook or workflow) and before cutting releases (e.g. as part of `/release-review` or `make test-all`).
   - If any test in the extended regression suite fails, the push or release process must be blocked immediately with clear error reporting.

# Repository Context and Constraints

- **Project Config**: `pyproject.toml` defines `[tool.pytest.ini_options]` with `addopts`, markers (`slow`, `livecorpus`), and `testpaths`.
- **Convenience Targets**: `Makefile` defines `test`, `test-all`, `test-release`, and related targets.
- **Git Hooks**: The repository utilizes `pre-commit` configured in `.pre-commit-config.yaml` with hook types `default_install_hook_types: [pre-commit, pre-merge-commit]`.
- **Parallel Execution**: Tests run with `pytest-xdist` (`-n auto` bounded via root `conftest.py` to half of available CPUs, max 6 workers, with `--dist=worksteal`).
- **No Code-Pinning Tests**: All selected tests must test observable runtime behavior, exit codes, and output contracts. Do not select or write tests that inspect source code via `inspect`, `ast`, regex, or line counts.
- **Remote SSH Environment**: Do not output absolute paths; use plain repository-relative paths without `file://` schemes.

# Specific Tasks

1. **Test Selection & Pytest Configuration**:
   - Audit the core subsystems of `agent_workflows/` and curate a representative set of high-value test modules for `testpaths` in `pyproject.toml` that runs in under 30 seconds on 6 CPUs while exercising key functional paths.
   - Ensure bare `pytest`, `python3 -m pytest`, and `make test` execute this exact core set without configuration drift.
   - Configure marker and path overrides so that explicit target invocations (e.g., `make test-all` or `pytest tests/ -m ''`) reliably run the complete retained suite.

2. **Pre-Push Automation**:
   - Implement a robust `pre-push` hook mechanism.
   - Wire the hook through `.pre-commit-config.yaml` using a local hook configured with `stages: [pre-push]` so all contributors and agents inherit the gate via `pre-commit install --hook-type pre-push`.
   - Provide an equivalent standalone `.git/hooks/pre-push` script as an alternative option.
   - Ensure the hook triggers `make test-all`, streams clear progress to the terminal, and halts git push on non-zero exit codes.

3. **Release Integration**:
   - Verify alignment with the `/release-review` workflow and `make test-release` target.
   - Document the command interfaces and expected execution runtimes for developers and CI runners.

4. **Benchmarking & Validation**:
   - Measure and paste actual timing evidence (`time python3 -m pytest` and `time make test-all`) confirming the routine gate finishes in < 30 seconds on 6 CPUs.
   - Validate that intentionally introduced test failures in both tiers halt execution with accurate failure summaries.

# Deliverable Format

Return your complete solution, configuration diffs, hook implementations, benchmarking measurements, and instructions as a single **DOWNLOADABLE markdown (`.md`) file**. Include all code snippets, file diffs, and exact terminal commands needed to apply and verify the implementation.
## Workflow history
- 2026-10-16 superseded (aw set): superseded by unified prompts wazeo5 (tiers) and 4ul37x (pruning), merged with the opencode drafts
