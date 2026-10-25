- Id: bkr6b0
- Status: open
- Set: specaudit
- Priority: medium
- Work-Kind: followup
- Summary: Restore behavioral tests for spec 7ckptx criteria left unverified by the 2026-09-24 suite trim

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

Commit 19313eed7 deleted test_lane_prompt_purity, test_lane_submission_collection, test_lane_permission_posture, test_lane_retention, test_containment_predicates, test_missing_input_repair, test_lane_clean_base and others. Decision packet jwd22f carried 29 criteria forward from plan 4fodkt (run 2026-09-17, before the trim). At HEAD 5db4791c1 these 7ckptx criteria rest on deleted tests: A1 (prompt path pattern-match; only a wording check remains at test_oc_runipd.py:4674), A3, A4, A5b, A5c, A7 (path_is_worker_forbidden has no test), A11, A13, A15b, A17-A20. Restore behavioral coverage, then 7ckptx can move to implemented. (The 4h->8h/240m->480m drift was amended 2026-10-25, commit e11eaab04.)
