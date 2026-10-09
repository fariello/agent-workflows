- Id: 8o7gco
- Status: open
- Blocks-Release: next
- Set: 8o7gco
- Priority: high
- Work-Kind: bug
- Summary: Checkout-local git identity was overwritten to Test <test@example.com>; 317 real commits since 2026-10-08 01:31 carry the test identity

## Workflow history
- 2026-10-09 created (aw backlog): Checkout-local git identity was overwritten to Test <test@example.com>; 317 real commits since 2026-10-08 01:31 carry the test identity

MEASURED 2026-10-09: this checkout's .git/config carries [user] name = Test, email = test@example.com (shadowing the global identity), and git log shows 317 commits authored 'Test <test@example.com>' since 2026-10-08 01:31:49 (first: 80c8a93d8, AW-Run run-20261007T182117Z-1726614, AW-Item w89bo8, which ran the bare suite plus 'python3 -m pytest -m slow' in its lane). Commits by the real identity stop at 01:31:02. That is exactly the identity tests/support.init_repo writes ('git config user.email test@example.com' / 'user.name Test'), so the likeliest cause is a test, plausibly a slow-marked one, running a git config in a cwd that resolved to the real checkout rather than a fresh temp repo; it is not yet pinned to a test. Worktrees share .git/config with the main checkout, so a lane-local write reaches main. Effects: wrong provenance on runner and agent commits (lifecycle, integrate, work); a test that commits in a fresh repo without its own identity now fails here (tests/test_attempt_lane_facts.py::test_case_2_oc_host_refused_isolated_turn fails 'git commit' in the real checkout context). Needs: (1) maintainer decides whether to restore the local identity (remove the [user] block from .git/config) and whether to rewrite history (NOT recommended: published commits); (2) find the leaking test by running the suite with a guard that snapshots .git/config before and after; (3) add a session-level pytest fixture asserting the real checkout's git config is unchanged, so this fails loudly next time.
