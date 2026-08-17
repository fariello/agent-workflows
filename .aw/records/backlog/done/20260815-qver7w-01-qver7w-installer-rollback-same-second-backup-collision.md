- Id: qver7w
- Status: done
- Set: qver7w
- Priority: high
- Kind: bug
- Summary: run_rollback undo restores wrong index.md when two installs share a same-second backup timestamp (test_rollback_undo ~50% flake)

## Workflow history
- 2026-08-15 created (aw backlog): run_rollback undo restores wrong index.md when two installs share a same-second backup timestamp (test_rollback_undo ~50% flake)
- 2026-08-15 set (aw backlog): status -> done

test_installer.InstallerEndToEndTests.test_rollback_undo flakes ~50% (6/12 fail) under plain unittest AND pytest -n auto; passes when the two installs cross a 1s boundary. Root cause: engine.py backup dirs are keyed on a seconds-granularity timestamp (%Y%m%d-%H%M%S at :1620/:1712/:2227/:2591). When install 1 (fresh) and install 2 (overwrite) run within the same wall-clock second they collide into ONE backup dir; install 2's backup of the modified index.md does not overwrite install 1's already-backed-up original, so --undo restores install-1 content instead of the pre-second-install 'MODIFIED CONTENT', failing the assertion at test_installer.py:434. Distinct from the 2f261ec test_undo_prompts fix (that handled record-less latest dir selection in run_rollback; this is a same-second collision between two separate install runs). Likely fix: sub-second/monotonic backup dir suffix or per-install unique backup dir; needs a deterministic regression test (mutation-probed) and, because it is rollback-fidelity (safety-adjacent), likely its own corrective IPD rather than a hand-patch. Found while capturing the plan-11 self-migration baseline.
