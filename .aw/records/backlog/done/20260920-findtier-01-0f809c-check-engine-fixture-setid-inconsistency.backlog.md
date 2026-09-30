- Id: 0f809c
- Status: done
- Graduated-To: findtier
- Set: findtier
- Priority: low
- Work-Kind: chore
- Summary: Four check_engine test fixtures declared a Set contradicting their own filename, masking name-vs-metadata coverage

## Workflow history
- 2026-09-30 set (aw backlog): closed by aw oc run: IPD y43g6q executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260928-findtier-01-y43g6q-pin-the-name-versus-metadata-set-agreement-the-trimmed-suite.ipd.md); evidence .aw/records/plans/executed/20260928-findtier-01-y43g6q-pin-the-name-versus-metadata-set-agreement-the-trimmed-suite.ipd.md
- 2026-09-28 set (aw backlog): graduated by run run-20260928T235632Z-1358353: y43g6q
- 2026-09-20 created (aw backlog): Found while executing findtier Order 02 (3i6rso). Four rows in tests/test_check_engine.py::CollisionTests carried fixtures whose declared '- Set:' disagreed with their own filename's setid segment (e.g. a plan named ...-demo-01-aaa111-p.ipd.md declaring '- Set: topic'). None of those rows is about name-vs-metadata agreement; the mismatch was incidental. It went unnoticed because no rule checked a record's declared Set against its filename until now. 3i6rso corrected the four filenames so each fixture carries only the defect its row claims (DECISION 04-3i6rso-D4). Filed as a chore rather than a bug because no user-visible behavior was wrong: the rows still asserted their intended properties. Worth a broader sweep of other fixture trees for the same latent inconsistency.
