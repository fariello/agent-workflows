- Id: raxuyq
- Status: done
- Blocks-Release: next
- Set: raxuyq
- Priority: high
- Work-Kind: bug
- Summary: aw specs note and aw specs set silently DELETE all but the newest tracked inline workflow-history round, and the sidecar they redirect it to is gitignored, so the dropped rounds (including --by-human approval attestations) have no tracked home anywhere

## Workflow history
- 2026-09-23 done (aw set): Already FIXED by executed plan vhbvwz (setterguard Order 02, commit fbf85068), which reversed the slimming in specs._append_history and backlog._reattach_history so both PREPEND and PRESERVE prior rounds. Verified live at HEAD 22cf67d9 by probing specs._append_history on a 3-round fixture: 4 rounds out, all 3 priors intact. The maintainer's 2026-09-10 ruling (vhbvwz OQ-01) made inline history the DURABLE home for specs and backlog items, matching plans, so this item's fix-option (a) (re-track the gitignored sidecar) is settled against. Closed via the SATISFIED path. What SURVIVED this family is tracked by IPD 7jqev2 (histresid): the migration slimmer, the oldest-first legacy reader, and the missing specs dedup.
- 2026-09-19 created (aw backlog): aw specs note and aw specs set silently DELETE all but the newest tracked inline workflow-history round, and the sidecar they redirect it to is gitignored, so the dropped rounds (including --by-human approval attestations) have no tracked home anywhere

FOUND BY plan n4xq3l, 2026-09-19, while discharging the Section 12a re-review obligation of spec uonrjg. The plan mandated aw specs note; running it destroyed five tracked history rounds of a release-gating spec, including its --by-human approval attestation. They were restored by hand in the same commit (DECISION 02-n4xq3l-D1), which is why no history was actually lost this time.

MEASURED 2026-09-19 on a COPY of the uonrjg spec (5 inline rounds), at HEAD 8fd2658a:

    $ aw specs note <copy> --message "PROBE: does note preserve prior rounds"
    aw specs note: appended a history record to <copy>
    $ grep -c "^- " <history section of copy>
    1            # was 5; four rounds gone, and the newest was replaced

    $ grep -c uonrjg .aw/records/history.jsonl
    1            # ONLY the probe record. The four dropped rounds are in NO sidecar.

WHY IT IS A DEFECT RATHER THAN THE DESIGN. The slimming ITSELF is sanctioned: spec 20260818-1525-02 R2 and its maintainer-RESOLVED OQ-2 (2026-08-18) say "KEEP THE LATEST ONE line inline ... full chronological log lives in .aw/records/history.jsonl", implemented by awhistory Order 02 (plan b0behn) in specs._append_history (agent_workflows/specs.py:342-365). The defect is that the PREMISE of that resolution no longer holds. Commit 0c82cbdb ("chore(gitignore): history.jsonl untrack") git rm --cached the sidecar and added records/history.jsonl to .aw/.gitignore two days later, on separate repo-hygiene grounds, and the retired plan for that change (.aw/records/plans/not-executed/20260820-awhistignore-01-pprchd-...) states in its own Scope that it "Does NOT touch ... the record_history writer/reader behavior". So nobody revisited the writer. The result is a slimmer that deletes durable, committed, human-attested history and relocates it to a file that is never committed. On a fresh clone the dropped rounds do not exist at all.

BLAST RADIUS: every spec and every backlog item in every managed repo, on every status write. Three writers share the behavior: specs.run_set, specs.run_note (both via specs._append_history), and backlog._reattach_history (hist_block = new_record, which drops old_hist). PLANS ARE EXEMPT and deliberately so (ipd_lint IPD-S405 requires the inline executed round), which is the precedent showing inline history is understood to be load-bearing where a gate reads it. Measured: 7 specs in this tree still carry multi-round inline history (max 11 rounds) and will be slimmed to 1 on their next tooled write.

IT ALSO CONTRADICTS A SHIPPED SPEC CONTRACT. .aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md states at F6 and again at A8 that "aw specs note appends one history record and changes nothing else". It does not: it also deletes every older round.

SUGGESTED FIX, one of three, maintainer to choose. (a) TRACK THE SIDECAR again (revert 0c82cbdb intent), which restores OQ-2 premise; weigh against the hygiene reason it was untracked (a dirty tree on every aw write, and local operational detail in a public repo). (b) STOP SLIMMING and keep full inline history for specs/backlog, as plans already do; costs file size, preserves everything, and makes F6/A8 true again. (c) SLIM ONLY WHAT IS ALREADY IN A TRACKED HOME, i.e. refuse to drop a round the sidecar cannot durably hold, which preserves both intents but needs the sidecar question answered anyway. RECOMMENDED: (b) for correctness of the tracked record, since a --by-human approval attestation is exactly the evidence AGENTS.md treats as unforgeable, and deleting it on an unrelated note write is a data-loss bug that no gate currently catches.
