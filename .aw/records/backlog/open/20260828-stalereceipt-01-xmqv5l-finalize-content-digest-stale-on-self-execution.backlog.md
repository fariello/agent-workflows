- Id: xmqv5l
- Status: open
- Blocks-Release: next
- Set: stalereceipt
- Priority: high
- Kind: bug
- Summary: aw ipd finalize self-execution deadlock: begin freezes a whole-file plan_content_digest, but executing an IPD REQUIRES editing that same file (mark E performed / fill V evidence), so the digest always goes stale and finalize/merge-back refuses 'stale receipt' on every self-finalizing run

## Workflow history
- 2026-08-28 created (aw backlog): aw ipd finalize self-execution deadlock: begin freezes a whole-file plan_content_digest, but executing an IPD REQUIRES editing that same file (mark E performed / fill V evidence), so the digest always goes stale and finalize/merge-back refuses 'stale receipt' on every self-finalizing run

ROOT CAUSE: ipd_lifecycle.receipt_is_current (ipd_lifecycle.py:580-586) invalidates a begin receipt when receipt['plan_content_digest'] != plan_content_digest(current_text), and plan_content_digest (:254-256) is a sha256 over the plan's EXACT bytes. begin() (:594+, receipt written :729-730) freezes BOTH a requirement_digest (scope/requirements) AND this whole-file content digest.

CONTRADICTION: executing an IPD MUST mutate the same plan file - the execution-state rule requires marking 'E-0N: performed', the validation-state rule requires filling 'V-0N Observed evidence' + Result: pass. So a correct execution ALWAYS changes the plan bytes, which ALWAYS staleness-invalidates the receipt. Therefore finalize (and emus4n's merge-back-to-main via execute_merge_and_revalidate_gate) refuses with 'the begin receipt is STALE: the plan content changed since begin; re-run aw ipd begin' on EVERY self-finalizing run.

OBSERVED: 7kbtkw run-20260829T004753Z: work done+verified on lane aw/lane/7kbtkw (commit 4a5febc, lane even self-finalized at 9fc2947), but merge-back refused stale -> left substantially-complete, not integrated to main, plan stuck in pending/. p7peqf/emus4n/pky603/bja8og only reached executed/ because I hand-finalized AFTER content settled with a FRESH begin immediately before finalize.

FIX (direction): the receipt must bind only invariants that legitimately must not change mid-execution - the requirement_digest (Scope-Paths + requirements) and base HEAD - NOT the whole-file byte digest. Options: (a) drop plan_content_digest from receipt_is_current, relying on requirement_digest + base-HEAD + finalize scope reconciliation; or (b) digest only the FROZEN region (metadata/Scope-Paths/requirements), explicitly excluding the mutable checklist (E/V states, Observed evidence, Workflow history). Then a normal execution that only edits checklist/evidence/history keeps the receipt valid; a change to scope/requirements still correctly invalidates it. Add a regression test: begin -> mark all E performed + fill V evidence + append workflow history -> finalize succeeds (no stale refusal); and begin -> edit Scope-Paths -> finalize still refuses stale.

IMPACT: this is THE reason whole IPD sets sit at approved/complete/partial instead of executed and require manual babysitting; it defeats driver self-finalize (ctt412) and worktree merge-back (emus4n) in the common case.
