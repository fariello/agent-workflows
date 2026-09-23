- Id: 1ffh63
- Status: open
- Set: 1ffh63
- Priority: low
- Work-Kind: followup
- Summary: Plan kl18sz F-7 declared a replay source unsatisfiable without checking dangling objects, so a review can retire recoverable evidence

## Workflow history
- 2026-09-22 created (aw backlog): Plan kl18sz F-7 declared a replay source unsatisfiable without checking dangling objects, so a review can retire recoverable evidence

MEASURED 2026-09-23 while executing plan `kl18sz`.

THE CLAIM. That plan's review finding F-7 (PR-001, a BLOCKER) states `aw/lane/8u6770` is 'ABSENT from all 125 lane branches', concludes the mandatory 13-file replay 'cannot be reconstructed from it', and re-points V-01 at a smaller 4-path substitute plus a labelled synthetic fallback.

THE HALF THAT IS RIGHT. The BRANCH REF really is gone. Re-measured at execution: 94 `aw/lane/*` refs and neither `aw/lane/8u6770` nor `aw/lane/lc4unl` among them; `aw/lane/lc4unl_attempt2` exists but carries ZERO work (`git merge-base main aw/lane/lc4unl_attempt2` equals its own tip `223474b0`, diff 0 paths), so the sanctioned substitute was ALSO unusable.

THE HALF THAT IS WRONG. A deleted branch ref does not delete its commits. `git fsck --lost-found` lists 509 dangling commits here, four of which name `8u6770`, including its finalize tip `0abc01d9` ('lifecycle(8u6770): finalize 8u6770 -> executed') whose history contains `b6b2afc0` ('records(8u6770): backfill Priority and Work-Kind on 57 pending plans by inheritance'). `git merge-tree --write-tree main 0abc01d9` reproduces a REAL 34-path conflict set. So the replay the review called unsatisfiable was satisfiable, at LARGER scale than the 13 paths originally claimed, and the execution used it instead of the substitute.

WHY IT IS WORTH FILING RATHER THAN SHRUGGING AT. The finding's remedy WEAKENED a validation item (a 4-path substitute, with a synthetic fixture as fallback) on a false premise, and the plan's own rule says a synthetic fixture presented as the real replay FAILS V-01. A reviewer reaching for `git branch -a` and stopping there will keep making this trade. The generalizable fix is a convention or a helper: before declaring lane evidence unrecoverable, search dangling objects by subject, because `git branch -a` answers a question about REFS and the evidence lives in OBJECTS.

HONEST LIMITS. Dangling objects are LOCAL and expire: `git gc` prunes them (default 90 days for unreachable), they are not cloned, and another checkout of this repository may not have them. So a dangling commit is a legitimate replay source when it resolves and is NOT a durable archive, and any convention written here must say so rather than implying lane evidence is permanent.

Raised by an executor during a non-interactive `aw oc run` turn.
