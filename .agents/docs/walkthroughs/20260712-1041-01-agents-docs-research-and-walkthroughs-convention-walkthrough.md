# Walkthrough: `.agents/docs/` convention (research + walkthroughs)

Date: 2026-07-12
Plan Executed: [.agents/plans/executed/20260712-0033-01-agents-docs-research-and-walkthroughs-convention.md](file://<repo-root>/.agents/plans/executed/20260712-0033-01-agents-docs-research-and-walkthroughs-convention.md)
Status: EXECUTED

---

## Part 1: Summary of Accomplishments

We have standardized the directory structure and naming conventions for durable knowledge (reference research and narrative execution walkthroughs) across the repository.

### Changes Made

#### 1. Category-1 Templates for Directory READMEs
* Created three templates under `.agents/workflows/templates/` to document the directories:
  * **[agents-docs-README.md](file://<repo-root>/.agents/workflows/templates/agents-docs-README.md)** (for `.agents/docs/`)
  * **[agents-docs-research-README.md](file://<repo-root>/.agents/workflows/templates/agents-docs-research-README.md)** (for `.agents/docs/research/`)
  * **[agents-docs-walkthroughs-README.md](file://<repo-root>/.agents/workflows/templates/agents-docs-walkthroughs-README.md)** (for `.agents/docs/walkthroughs/`)

#### 2. Engine and CLI Infrastructure
* **Constants**: Defined `DOCS_DIR` and `DOCS_SUBDIRS`.
* **README Generation**: Implemented `ensure_docs_readmes()` mirroring `ensure_plans_readmes()` and wired it into both `install_into_repo()` and the CLI run loop main path.
* **Directory Scaffolding**: Updated `create_setup_artifacts()` to create `.agents/docs/research/` and `.agents/docs/walkthroughs/` with committed `.gitkeep` placeholder files.

#### 3. Migration of Reference Files
* Migrated existing research documents from `docs/research/` (now deleted) to `.agents/docs/research/` using standard naming conventions:
  * **[20260712-0031-01-agent-instruction-file-discovery-survey.md](file://<repo-root>/.agents/docs/research/20260712-0031-01-agent-instruction-file-discovery-survey.md)**
  * **[20260712-0031-02-agent-instruction-file-discovery-prompt.md](file://<repo-root>/.agents/docs/research/20260712-0031-02-agent-instruction-file-discovery-prompt.md)**

#### 4. Filename Normalization and Naming Checks
* Updated `.agents/workflows/setup-repo/tools/normalize_plan_names.py` to scan the `docs` area by default and recognize its subdirectories.

#### 5. Guidelines and Rule Mirroring
* Updated `agents_pointer_block()` in the installer and the root **[AGENTS.md](file://<repo-root>/AGENTS.md)** to instruct future coding agents to save research and walkthroughs under `.agents/docs/` with canonical names.

---

## Part 2: Verification & Testing

### 1. Unit & Integration Tests
* Added tests in `tests/test_setup_artifacts.py` verifying the creation of docs subdirectories, gitkeep placeholders, and templates.
* Added `test_docs_scanned_by_default_area_narrows` to `tests/test_normalize_plan_names.py` verifying the normalizer scans docs and respects narrow/area arguments.
* All 206 unit and integration tests are passing successfully.

### 2. Manual Verification
* Ran the normalizer script (`normalize_plan_names.py`) to confirm no conformant file issues exist.
