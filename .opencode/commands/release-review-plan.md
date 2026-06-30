---
description: Run the audit and planning phases of the release review without implementation
agent: build
---

Read and execute @release-review/README.md in planning-only mode.

Planning-only mode means:

1. Complete run setup.
2. Complete Section 1 serially.
3. Complete Sections 2 through 6, using controlled parallel read-only audit lanes when useful.
4. Create or update all required run artifacts for Sections 1 through 6.
5. Create `repository-review/<RUN_ID>/09-implementation-plan.md`.
6. Do not perform Section 7 implementation.
7. Do not edit tracked project files except to remove a stale `repository-review/` line from `.gitignore` so the run artifacts can be tracked.
8. Run artifacts (`repository-review/<RUN_ID>/`) are committed deliverables; commit the planning-phase artifacts. Do not make product-code commits in planning-only mode.
9. Do not push to a remote.
10. Stop after producing a planning-only summary that explains the proposed implementation plan and asks the user to run `/release-review` to continue or explicitly approve implementation.
