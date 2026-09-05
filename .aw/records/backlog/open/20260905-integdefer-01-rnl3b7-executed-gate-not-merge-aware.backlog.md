- Id: rnl3b7
- Status: open
- Set: integdefer
- Priority: high
- Work-Kind: bug
- Summary: the executed-transition pre-commit gate has no merge-aware path, so it refuses every legitimate integration of an already-finalized lane

## Workflow history
- 2026-09-05 created (aw backlog): the executed-transition pre-commit gate has no merge-aware path, so it refuses every legitimate integration of an already-finalized lane

THE DEFECT. The `ipd-executed-transition-gate` pre-commit hook
(`agent_workflows/hooks/executed_transition_gate.py`) refuses any commit in which a plan arrives in
`.aw/records/plans/executed/` unless a finalize transaction journal exists under
`.aw/state/runtime/transactions/ipd_finalize_<id6>.json`. That predicate cannot be satisfied by a
LANE MERGE, for a structural reason: `.aw/state/` is gitignored box-local state, so the journal
never travels with a lane branch, and the lane worktree that held it is torn down after integration.

So the hook cannot distinguish the abuse it was built to catch (hand-editing a plan's `- Status:` or
`git mv`-ing it into `executed/`) from the legitimate act of merging a lane on which
`aw ipd finalize` genuinely ran. It refuses both.

MEASURED, 2026-09-05. Recovering five lanes stranded by `run-20260905T050043Z-639569` required
`--no-verify` on four of the five merges (`eyh1fu`, `txc9l1`, `uyeko5`, `eulhzt`), each with
maintainer authorization and each documenting the bypass in its commit message. In every case finalize
HAD run on the lane, provably: commits `c9db21a3`, `43c87af5`, `251b7399`, `dd996d73`, all
titled "lifecycle(<id6>): finalize <id6> -> executed".

EVIDENCE THE HOOK DOES NOT MODEL MERGES AT ALL, not merely that it lacks the journal: the FIRST of
those five merges (`76gsmv`) PASSED the hook. Same situation, same missing journal, opposite outcome -
because git recorded that plan file as a RENAME rather than an addition, so the hook's staged-change
inspection did not classify it as a plan-to-executed transition. A gate whose verdict depends on
whether git chose rename detection is not gating the property it claims to gate.

WHY THIS MATTERS BEYOND THE INCONVENIENCE. A gate that must be bypassed as ROUTINE PRACTICE teaches
operators and agents that `--no-verify` is normal, which is precisely how a real hand-edit bypass
would later slip through unremarked. The hook's own docstring is honest that it is local best-effort
prevention, skippable, with `aw check`/`aw doctor` as the deterministic backstop - but "skippable"
was meant as a limitation, not as the expected workflow.

DIRECTION FOR A FIX (not prescribed; needs design).
  * MERGE AWARENESS: during a merge (`.git/MERGE_HEAD` present), a plan arriving in `executed/`
    whose incoming side carries a `lifecycle(<id6>): finalize` commit is a legitimate integration.
    That commit is IN-TREE evidence, unlike the gitignored journal, so it survives the branch.
  * OR make the evidence portable: if the finalize journal (or a redacted attestation of it) were
    committed rather than gitignored, the predicate would work across trees by construction. Weigh
    against why `.aw/state/` is gitignored in the first place.
  * EITHER WAY, keep the hand-edit case refused. The goal is to stop refusing legitimate merges, NOT
    to weaken the gate. A fix that simply exempts all merges would let someone stage a hand-edit
    inside a merge commit.
  * Fix the rename-vs-add inconsistency regardless, since it makes the current gate's behavior
    arbitrary.

RELATED. This is the same family as `5wdoze` (integration deferral ladder), `p8ni63` (startup
dirty-base gate) and `yocdq4` (`aw <host> integrate` verb): all four are friction on the path
between a verified lane and main. `yocdq4` in particular should be built with this in mind - a
re-integrate verb that trips this hook on every invocation would be unusable, so whichever lands
second must account for the first.
