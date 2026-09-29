- Id: zf1m48
- Status: open
- Blocks-Release: next
- Set: structpin
- Priority: medium
- Work-Kind: bug
- Summary: tests/test_walkthrough_id6.py pins a literal 24-walkthrough census over the live records tree, so the next walkthrough any agent writes turns the default suite red

## Workflow history
- 2026-09-28 created (aw backlog): tests/test_walkthrough_id6.py pins a literal 24-walkthrough census over the live records tree, so the next walkthrough any agent writes turns the default suite red

MEASURED 2026-09-28 at HEAD a314c925. `tests/test_walkthrough_id6.py::TestWalkthroughDeclaredIdMatchesSlot::test_clustered_walkthroughs_declare_matching_id` asserts `len(all_files) == 24` ("Census must find exactly 24 walkthroughs") and `len(exempt) == 11` over the LIVE `.aw/records/walkthroughs/` tree. The tree holds exactly 24 non-README walkthroughs right now, so the count is AT its pin and the next walkthrough written trips it.

WHY THIS IS A BUG AND NOT A CHORE, on the user-perceptible-impact test: AGENTS.md REQUIRES agents to write walkthroughs, so this test penalizes the required behavior. The file carries NO `livecorpus` marker (verified: no `pytestmark`, no marker anywhere in the file), so it runs in the DEFAULT suite, which `pyproject.toml` scopes with `-m "not slow and not livecorpus"`. A red test here therefore blocks every concurrent lane integration, which is exactly the hazard the `livecorpus` marker exists for and which `pyproject.toml` records as having cost "2h 10m and $55.02 with nothing integrated" on 2026-09-19.

THE FIX IS SUBTRACTION, NOT RE-NUMBERING. The real invariant is already asserted in the same test: `assertEqual(missing_or_mismatched, [], ...)`, which checks that every clustered walkthrough declares an `- Id:` matching its filename identity slot. That assertion needs neither literal. Bumping 24 to 25 reproduces the defect one walkthrough later.

RELATED BUT DISTINCT: plan `b02ohu` (Set `structpin`, from backlog `5zyuc8`) sweeps the CODE-STRUCTURE pins and explicitly defers this one, because this is a census over the RECORDS tree rather than over code structure, and widening that plan would have been opportunistic scope growth. The `LEGACY_WALKTHROUGHS` set of 11 names and the `BULLETLESS_GRANDFATHERED` set are separate grandfathering data and are NOT themselves the defect; only the two literal length assertions are.
