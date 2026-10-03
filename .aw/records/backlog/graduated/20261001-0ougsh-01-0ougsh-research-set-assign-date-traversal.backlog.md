- Id: 0ougsh
- Status: graduated
- Graduated-To: 0ougsh
- Blocks-Release: next
- Set: 0ougsh
- Priority: medium
- Work-Kind: bug
- Summary: aw research set-assign interpolates an unvalidated --date into the destination filename, so a traversal in it moves an existing record outside the records tree; measured 2026-10-01, the sibling vector to m5csyi on the rename path

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: plb8jx
- 2026-10-01 created (aw backlog): aw research set-assign interpolates an unvalidated --date into the destination filename, so a traversal in it moves an existing record outside the records tree; measured 2026-10-01, the sibling vector to m5csyi on the rename path

FILED WHILE AUTHORING plan `deftzy` (Set `7w6zsl`), which fixes the research tree's descriptive-field injection and deliberately excludes every `--date` defect.

MEASURED 2026-10-01 in a lane at HEAD `9e813570a`, against a temporary fixture nested four levels deep so the escape lands somewhere writable (see the FALSE-NEGATIVE warning below).

`aw research set-assign <id6> --set esc --date ../../../../ESCAPED --apply` exits **0** and prints `renamed .aw/records/research/20261001-tv-00-hpdv9t-tv.findings.md -> .aw/records/research/../../../../ESCAPED-esc-00-hpdv9t-tv.findings.md`. Verified on disk: the file landed FOUR DIRECTORIES ABOVE the repository root, outside the records tree and outside the repo, and the repository's own research directory is now empty (the following `aw research index` reported `(0 docs)`).

THIS IS WORSE THAN THE CREATION-PATH TWIN AND THAT IS WHY IT IS FILED SEPARATELY. `m5csyi` measures `aw research new --date <traversal>` CREATING a new file outside the tree, which loses nothing that existed. This verb MOVES an EXISTING committed record out of the repository, so a single mistyped or hostile `--date` on a regroup silently removes a tracked artifact from the tree while exiting 0. Nothing in the output says the destination left the repo.

WHY `m5csyi` DOES NOT ALREADY COVER IT: that item measures and prescribes a fix for `research new` only, and the two paths derive their destination through different code. `research_cmd.plan_new` builds the name from `date_str` directly; this verb goes through `research_refs.plan_set_assign`, which takes `date_str` from `run_set_assign`'s `getattr(args, "date", None) or date.today().strftime("%Y%m%d")` and feeds it into `R.ResearchName`. A guard added only to `plan_new` leaves this open. Whichever fix shape `m5csyi` (or plan `ribg85`, which ports the sibling fix to `specs.run_new`) settles on should be REUSED here rather than re-litigated.

RE-MEASURING THIS NEEDS A NESTED FIXTURE OR YOU WILL GET A FALSE NEGATIVE, for exactly the reason `m5csyi` records: with the fixture directly under a shallow temp directory the escape can land on a non-writable parent and the command fails with `Permission denied`, which looks like a guard and is not one. Nest the fixture (`<tmp>/a/b/c/repo`) so the escape lands somewhere writable.

A PLAIN NEWLINE IN `--date` IS A SECOND, DISTINCT OUTCOME ON THIS VERB and is NOT the injection `deftzy` fixes: driven with `--date $'20261002\nstatus: active'`, this verb produces a name the grammar REJECTS (`name-invalid: core must be 'YYYYMMDD-<set-id>-<NN>-<id6>-<slug>'`) and still performs the rename, leaving a record whose filename contains a literal newline. The corresponding `aw research new --date` newline injects front-matter KEYS as well, which is why `deftzy` names `--date` as excluded rather than silently covered: `attention_contract.is_safe_descriptive('../../../../ESCAPED')` returns **True**, so the descriptive-field predicate provably cannot detect a traversal. The fix class is date-format validation plus destination containment.
