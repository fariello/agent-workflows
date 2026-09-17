- Id: no0j8g
- Status: open
- Set: no0j8g
- Priority: low
- Work-Kind: chore
- Summary: Four aw attention tests passed dir=None and so read the developer's real repository, making their exit codes depend on live repo state

## Workflow history
- 2026-09-17 created (aw backlog): Four aw attention tests passed dir=None and so read the developer's real repository, making their exit codes depend on live repo state

MEASURED by plan pr5b0t (lanestrand-01) when adding a new run-record-backed reader to aw attention: four tests in tests/test_attention.py went red, not because the reader was wrong, but because they had been reading the DEVELOPER's real repository all along and had simply never had a reason to notice.

THE TESTS: test_run_status_filtering_in_att_run, test_id6_only_output_in_att_run, test_paths_and_filenames_output_in_att_run, test_active_and_not_active_filtering_in_att_run.

THE SHAPE OF THE PROBLEM: each mocks attention.scan (so the ITEMS are hermetic) but passes dir=None in its argparse namespace, which resolve_verb_repo_root resolves to the actual project root. Anything in attention.run that consults the repo for something other than scan() therefore reads live state. Adding one such consultation flipped all four exit codes from 0 to 1.

WHAT pr5b0t DID: stubbed the new reader in those four tests, with the reason recorded in a comment, because rewriting four unrelated tests was outside its scope.

THE REAL FIX: give those cases a temp dir (they already build Items by hand, so nothing needs a real tree), or make the harness refuse dir=None so the coupling cannot be reintroduced silently. The current state is a latent trap: the NEXT repo-consulting feature added to attention.run will break the same four tests for the same non-reason.
