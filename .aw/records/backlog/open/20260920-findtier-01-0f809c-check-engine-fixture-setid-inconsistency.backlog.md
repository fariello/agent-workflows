- Id: 0f809c
- Status: open
- Set: findtier
- Priority: low
- Work-Kind: chore
- Summary: Four check_engine test fixtures declared a Set contradicting their own filename, masking name-vs-metadata coverage

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing findtier Order 02 (3i6rso). Four rows in tests/test_check_engine.py::CollisionTests carried fixtures whose declared '- Set:' disagreed with their own filename's setid segment (e.g. a plan named ...-demo-01-aaa111-p.ipd.md declaring '- Set: topic'). None of those rows is about name-vs-metadata agreement; the mismatch was incidental. It went unnoticed because no rule checked a record's declared Set against its filename until now. 3i6rso corrected the four filenames so each fixture carries only the defect its row claims (DECISION 04-3i6rso-D4). Filed as a chore rather than a bug because no user-visible behavior was wrong: the rows still asserted their intended properties. Worth a broader sweep of other fixture trees for the same latent inconsistency.
