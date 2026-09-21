- Id: l2mzxn
- Status: done
- Set: l2mzxn
- Priority: high
- Work-Kind: bug
- Summary: make_integration_validation_runner reads lane base/head from item keys that a first attempt never has, so the post-merge revalidation gate refuses every isolated item as merge-conflict without running the suite

## Workflow history
- 2026-09-21 done (aw set): FIXED in 3324d339. resolve_lane_endpoints() now reads the lane from attempt['worktree_base']/['worktree_branch'] (present during the turn, which is when the gate asks) and keeps the preserved_* fields as the fallback for a later caller. Two tests added in tests/test_suite_adjudication.py: one built from the actual first-attempt call-site shape, proven falsifiable against the pre-fix resolution (fails with 'AssertionError: False is not true'), asserting the suite actually RUNS rather than only that the verdict is True; one pinning the attempt-over-preserved precedence. Suite 7993 passed, 3 skipped, 2 xfailed (baseline 7991 passed, same 0 failures, delta is the two new tests). The three lanes the defect stranded (i1hlgx, k9awrq, quqyc4) were merged first; the combined tree measured 7991 passed, confirming the 'combined-red' refusal was false. De-gated rather than handed off: the bug is fixed in-tree, so it no longer gates the release. TWO RESIDUAL ITEMS DELIBERATELY NOT FIXED HERE, since both are judgement calls about the ladder's vocabulary rather than this resolution defect: the ladder treats this refusal class as terminal on first attempt, so an unresolvable-endpoints refusal is never retried even though a retry would now succeed; and 'merge-conflict' remains the operator-facing label for a refusal involving no git conflict, which is what made this take a full diagnosis to identify. File those separately if they should change.
- 2026-09-21 created (aw backlog): MEASURED 2026-09-21 diagnosing run-20260921T105933Z-1994623, where items i1hlgx, k9awrq and quqyc4 each finished 'merge-conflict' after a full successful agent turn.

NOT A GIT CONFLICT. All three lane branches merge cleanly into main: 'git merge-tree --write-tree main aw/lane/<id6>_attempt2' exits 0 with no conflict for each. The status is the integration ladder's label for a fail-closed refusal class, and the actual refusal recorded in state.json is post_merge_revalidation.reason = "the lane's base/head could not be resolved from run state (repo=True, base=False, head=False), so the merge result cannot be built; refusing (fail-closed)".

THE DEFECT. runner_shared.make_integration_validation_runner resolves the merge result's endpoints at runner_shared.py:13298-13299:

  base = str(item.get('preserved_base') or item.get('base_commit') or '')
  head = str(item.get('lane_head') or item.get('preserved_head') or '')

On a FIRST attempt none of those four keys exist on the item:
  * 'preserved_base' is written only by lane_containment.record_preserved_lane_state (lane_containment.py:3502), on the POST-turn preservation path, which runs AFTER integration. The codebase already states this explicitly in a different context: runner_shared.py:16624-16631 warns that 'preserved_base' 'is written only on the POST-turn PRESERVATION path and only when the item did NOT reach executed, so it is absent for a first attempt', and for that reason the suite baseline deliberately reads attempt['worktree_base'] instead. The revalidation runner reads the field that comment warns against.
  * 'lane_head' and 'preserved_head' are written NOWHERE. grep -rn "lane_head\|preserved_head" agent_workflows/ returns exactly one hit, the read itself at runner_shared.py:13299. They are dead keys.
  * 'base_commit' is an ATTEMPT field (attempt['worktree_base'], runner_shared.py:16653), not an item field.

The head fallback at :13300-13305 (rev-parse item['preserved_branch']) is dead for the same reason: 'preserved_branch' is written by the same post-turn function.

CONSEQUENCE. With --validate OFF (the default; this run had validate=False, no_audit=True, isolate_worktree=True) the gate takes the SUITE-EARNED mode and calls this runner, which refuses before materializing anything. So the gate refuses EVERY isolated first-attempt execute item and the suite it exists to run is invoked ZERO times. This is not specific to the three plans: it is the default configuration.

REPRODUCED DIRECTLY, not inferred. Calling the factory with an item shaped as it is at the integration call site (only id6 + attempts[0].worktree_base/worktree_branch) returns verdict False with the injected suite_check invoked 0 times and the base=False, head=False reason recorded. The same call with preserved_base + preserved_branch present returns True, invokes the suite exactly once, and records tree 30dda0eabb8b. So the resolution is the whole defect; nothing downstream is wrong.

REGRESSION WINDOW. Introduced 2026-09-21 in ffd220bf 'fix(integration): revalidate the real merge result instead of returning True (daexj1)', which replaced a constant-True runner. Before it the gate always passed; now it always refuses in the default mode. tests/test_suite_adjudication.py covers the function only with preserved_base pre-populated on the item (:627, :788, :824), which is why a first-attempt shape was never exercised.

NO WORK WAS LOST, which is the fail-closed design working: all three lanes are preserved with their commits intact (5, 5 and 5 commits ahead of main respectively) and main is untouched.

A FIX MUST resolve base from attempt['worktree_base'] (the field the suite baseline already trusts for exactly this reason) and head from the live lane branch attempt['worktree_branch'] / the handle, and must be covered by a test built from the ACTUAL call-site item shape rather than a hand-populated one. Note the ladder also classifies this refusal as terminal on first attempt ('repetition cannot fix a conflict, stale base, combined-red revalidation, or scope violation'), so an unresolvable-endpoints refusal is not retried; whether that class deserves its own non-terminal kind, and whether 'merge-conflict' is the right operator-facing label for a refusal that involves no conflict, are worth deciding in the fix.
