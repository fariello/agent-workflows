- Id: muqwhb
- Status: open
- Set: fastsuite
- Work-Kind: chore
- Priority: medium
- Summary: Adopt worker-scoped template git repo copies across test modules still calling git init per test method
- Short-Description: Adopt worker-scoped template git repo copies across test modules still calling git init per test method

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): Adopt worker-scoped template git repo copies across test modules still calling git init per test method

Measured 340 test files with 738 git init sites contributing heavily to ~20 CPU-minutes of kernel sys time during thorough-suite. Extend adoption of tests/repo_template.py::copy_template_repo (or tests/support.py::init_repo) across the highest-frequency per-test _make_test_repo/_init_repo helpers while keeping 100% isolated real git repos per test.
