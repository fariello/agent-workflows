- Id: es7wdp
- Status: open
- Set: scoperewrite
- Priority: low
- Work-Kind: chore
- Summary: Decide whether a record status transition should rewrite citing Scope-Paths entries, removing the cause of stale scope targets instead of grading the symptom

## Workflow history
- 2026-09-30 created (aw backlog): Decide whether a record status transition should rewrite citing Scope-Paths entries, removing the cause of stale scope targets instead of grading the symptom

RAISED as OQ-01 of plan guti33 (Set 9xap30), which graduated backlog 9xap30 and implements the SYMPTOM half: it re-tiers a plain moved check.scope-path-target-stale finding to info so a routine status transition stops setting an exit code. THIS ITEM IS THE CAUSE half, which is backlog 9xap30's option (c) and is a maintainer decision rather than something the repository answers.

THE CAUSE IS SINGLE-SOURCED AND MEASURED. status_set.apply_status_change is the ONE record-type-agnostic handler behind aw backlog set, aw specs set, aw ipd set and bare aw set. It computes a destination with record_placement.resolve_transition_path, relocates the file with _core.git_mv, rewrites many FIELDS on the moved record, and rewrites NO CITATION anywhere else. So a plan that declared the record at its old status directory is left pointing at a path that no longer exists.

THE REWRITER ALREADY EXISTS AND IS PROVEN. artifact_refs.plan_reference_rewrites plus apply_reference_rewrites, driven by an old-name-to-new-name map, fence-masking and permalink-masking aware, is what aw rename calls today. So option (c) is SMALLER than backlog 9xap30 suggests: it is 'call the existing rewriter from the existing setter', not new machinery.

THE HAZARD IS WHY THIS IS A DECISION AND NOT A CHORE TO JUST DO. That rewriter edits every citing file across REFERENCE_SCAN_ROOTS, which includes other plans. A plan mid-execution has a begin receipt freezing its Scope-Paths, and ipd_lifecycle.receipt_is_current treats a changed entry as invalidating ('a different Scope-Paths entry ... still invalidates the receipt'). So a routine aw backlog set graduated could stale an unrelated IN-FLIGHT plan's receipt and strand its lane at finalize. That is the exact class of loss measured in run run-20260917T023628Z-4108757 (three stranded items, 95.71 dollars, 3h10m) which rcptwiden 63425h exists to prevent. A safe implementation therefore needs a stated rule for in-flight plans (skip and report, or rewrite and re-freeze), which is a contract decision about what a setter is allowed to touch.

MEASURED EXPOSURE, so the decision is not abstract. 78 literal .aw/records/ Scope-Paths entries exist across pending plans (specs/approved 14, plans/executed 11, backlog/open 9, plans/pending 6, specs/implemented 5, backlog/done 4, plus singletons across reviews, research, walkthroughs, releases, roadmaps and four READMEs). FOUR were stale at the time of filing, every one a plain moved caused by a CORRECT backlog open -> graduated transition the runner itself performed (the graduated items' history lines read 'graduated by run run-20260928T235632Z-1358353: aisk5z' and 'graduated by run run-20260929T021205Z-3914774: 2misq5'). Backlog 9xap30 predicted this mechanism for SPECS; it arrived through BACKLOG items first, and backlog/open entries are the most volatile of all because graduating an item is routine.

THE ALTERNATIVE THAT NEEDS NO CODE. A status-agnostic glob is already a legal scope entry: .aw/records/backlog/**/<name>.backlog.md passes ipd_schema._scope_path_entry_error, survives parse_scope_paths, matches the file under open/, graduated/ and done/ via ipd_lifecycle._scope_match while correctly rejecting a different file in the same directory, and can never produce this finding because stale_record_scope_paths skips any entry containing a glob token. So one option is guidance rather than code: teach authors that spelling. That is a convention change for every plan author, which is why guti33 did not adopt it unilaterally.

NOT URGENT. After guti33 the symptom is a visible info advisory that sets no exit code, so nothing reds and no run is refused (the runner's dispatch refusal fires only on moved-terminal and vanished and is untouched). This item exists so the cause is not silently accepted as permanent.
