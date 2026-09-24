- Id: qliia1
- Status: done
- Set: qliia1
- Priority: high
- Work-Kind: followup
- Summary: 14 aw/lane/* branches hold commits that never reached main; the work needs triaging or deliberate discarding

## Workflow history
- 2026-09-24 done (aw set): Discharged by research record ebh1ap: full triage and disposition of the 14 lane branches
- 2026-09-17 created (aw backlog): 14 aw/lane/* branches hold commits that never reached main; the work needs triaging or deliberate discarding

MEASURED 2026-09-17 from the shared git object store (readable from any worktree), at main 1171f7b2:

    $ git for-each-ref --format='%(refname:short)' 'refs/heads/aw/lane/*' | wc -l   -> 38
    $ git for-each-ref --merged main --format='%(refname:short)' 'refs/heads/aw/lane/*' | wc -l -> 25
    unmerged, with 'git rev-list --count main..<branch>':
      aw/lane/03ie04   2      aw/lane/2c122z  26      aw/lane/58ha43  22
      aw/lane/7p9n2v  16      aw/lane/d7qoxv   1      aw/lane/fn2l1u   2
      aw/lane/mm5p3v   3      aw/lane/nna8yz   3      aw/lane/qcqhj7   3
      aw/lane/r2i1b1   1      aw/lane/rchpms  10      aw/lane/tx6q0h   -
      aw/lane/upgtest  3      aw/lane/ybkmzp   2

That is FOURTEEN lanes holding unintegrated commits, more than the eleven backlog nuanaw recorded, and two of them (2c122z at 26 commits, 58ha43 at 22) hold substantial work.

WHY THIS IS FILED RATHER THAN ACTED ON: plan pr5b0t (lanestrand-01) makes this VISIBLE (aw attention now reports each as STRANDED and --check fails closed on it), and its own contract is explicit that recovery is a human act and that it must not read, merge, prune or clean any real lane. So the alarm is built; the triage is not this plan's to perform.

WHAT THE WORK IS: for each branch, decide MERGE (the work is wanted) or DISCARD (superseded, or the plan was re-executed and this is the abandoned first attempt, e.g. the attempt-scoped clusters). Do not bulk-delete: some of these are the only copy of validated work. aw oc integrate does not exist yet (plan rl67b0 is still pending), so today the route is manual: git log main..<branch> to see the work, then merge.

NOTE some of these lanes ALSO have live worktrees under .aw/worktrees/, and other agents may be working in them concurrently; check before touching one.
