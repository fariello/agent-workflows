- Id: i8wmte
- Status: done
- Blocks-Release: next
- Set: i8wmte
- Priority: high
- Work-Kind: bug
- Summary: aw specs note DELETES the prior inline history record while reporting that it appended one, and for a spec with no - Id: the sidecar gets nothing either, so the record is lost outright

## Workflow history
- 2026-09-23 done (aw set): Already FIXED by executed plan vhbvwz (setterguard Order 02, commit fbf85068), which reversed the slimming in specs._append_history and backlog._reattach_history so both PREPEND and PRESERVE prior rounds. Verified live at HEAD 22cf67d9 by probing specs._append_history on a 3-round fixture: 4 rounds out, all 3 priors intact. The maintainer's 2026-09-10 ruling (vhbvwz OQ-01) made inline history the DURABLE home for specs and backlog items, matching plans, so this item's fix-option (a) (re-track the gitignored sidecar) is settled against. Closed via the SATISFIED path. What SURVIVED this family is tracked by IPD 7jqev2 (histresid): the migration slimmer, the oldest-first legacy reader, and the missing specs dedup.
- 2026-09-19 created (aw backlog): aw specs note DELETES the prior inline history record while reporting that it appended one, and for a spec with no - Id: the sidecar gets nothing either, so the record is lost outright

MEASURED 2026-09-19 while executing plan 0ta5vg E-07, which had to amend spec attention-registry-and-cross-tree-status via 'aw specs note' (the only surface permitted for an 'implemented' spec).

WHAT HAPPENS. 'aw specs note <spec> --message ...' prints 'appended a history record to <spec>' and then REPLACES the entire '## Workflow history' section body with the single new record, deleting every record that was there. On the real spec above, the existing 2026-09-17 record naming plan pr5b0t (which documented F3a's original introduction, the run-record-not-filesystem rule and the two normative exclusions) is GONE from the tracked file; 'grep -c pr5b0t' on the spec returns 0 where it returned 1.

WHERE. agent_workflows/specs.py:342 '_append_history'. Its own comment states the intent ('the inline section keeps only the LATEST record; the full chronological log lives in the global .aw/records/history.jsonl sidecar'), so truncation is deliberate; the defects are that the reported action contradicts the performed action, and that the fallback the design depends on is not reliable.

REPRODUCED IN ISOLATION, twice, on throwaway specs (not the real one):
  (a) spec WITH '- Id: aaa111': inline FIRST record deleted, one sidecar line written. Recoverable, but the CLI still says 'appended'.
  (b) spec WITHOUT '- Id:': inline FIRST record deleted and the sidecar line count did NOT change (1 -> 1). The prior record is destroyed with NO copy anywhere. This is the data-loss case.

WHY (b) BITES THE REAL SPEC. The amended spec 20260808-1945-01-attention-registry-and-cross-tree-status.spec.md has NO '- Id:' line (grep returns nothing; it is a pre-id6 legacy spec name, which AGENTS.md explicitly grandfathers). So specs most likely to carry long histories are exactly the ones whose history cannot be recovered.

COMPOUNDING FACTOR: .aw/records/history.jsonl is GITIGNORED (.aw/.gitignore:11) and therefore per-checkout and never shared. So even in case (a) the 'full chronological log' does not travel with the repository, is absent in a fresh clone and in every lane worktree, and cannot be consulted by a reviewer. The tracked file is the only durable carrier, and that is the one being truncated.

IMPACT. Spec history is the audit trail for a normative contract: which plan amended a clause, when and why. Losing it silently is worse than never having written it, because a reader sees a single record and concludes it is complete.

SUGGESTED FIX (not implemented here; out of plan 0ta5vg's scope): either APPEND to the inline section and keep the truncation opt-in, or keep truncating but (i) make the CLI say what it actually did rather than 'appended', (ii) refuse when no durable sidecar record can be written (no '- Id:'), and (iii) stop gitignoring the sidecar if it is genuinely the system of record.

NOT A REGRESSION THIS PLAN CAUSED, and plan 0ta5vg did not work around it: E-07 legitimately needed 'aw specs note' (a status transition is refused for an 'implemented' spec) and the amendment itself is correct and intact. The lost pr5b0t record is recoverable from git history ('git show HEAD:<spec>') and restoring it is left to this item so the plan's own diff stays inside its declared scope.
