- Id: hernns
- Status: open
- Blocks-Release: next
- Set: hernns
- Priority: medium
- Work-Kind: bug
- Summary: aw ipd finalize WITHOUT --apply completes a committed-incomplete transaction, consuming the begin receipt from a surface documented as a preview

## Workflow history
- 2026-09-29 created (aw backlog): Filed while authoring bn58ha's graduation plan; measured, see body.

MEASURED 2026-09-29 at HEAD d02e4e64, in a scratch git fixture reproduced twice plus once through the real CLI.

WHAT IS WRONG. `aw ipd finalize <plan> --actor ... --message ...` WITHOUT `--apply` is documented as a preview: `cli.py` registers `--apply` with the help text "Perform the transition (default: preview the precheck)", and `ipd_lifecycle.finalize`'s `if not apply:` arm returns "precheck + reconciliation passed; re-run with --apply to perform the terminal transaction". That contract holds only on the ORDINARY path. When a prior attempt left the finalize transaction journal in `PHASE_COMMITTED_INCOMPLETE`, `finalize` runs `_early_recovery_result` BEFORE it ever reaches the `apply` test, that helper calls `_resume_post_commit`, and the resume COMPLETES the transaction and returns. The `if not apply:` arm is never reached, so a surface the operator invoked as a preview performs a terminal, receipt-consuming state change.

MEASURED, three times on the same fixture shape (wedge `committed-incomplete` by forcing the `post-transition` lint to raise, leaving the plan already moved to `executed/` with its lifecycle commit made):
- before, in every trial: journal phase `committed-incomplete`, begin receipt PRESENT
- `finalize(..., apply=False)` -> exit 0, message `finalized abc123 -> executed at <sha> (actor opencode/test)`; after: journal `None`, receipt GONE
- `finalize(..., apply=True)` -> byte-identical outcome, so the two invocations are indistinguishable
- through the real CLI, `cli.main(["ipd","finalize","abc123","--actor",...,"--message",...])` with NO `--apply` -> prints `finalized abc123 -> executed at <sha>`, exits 0, and leaves journal `None` and the receipt consumed

WHY IT MATTERS. The begin receipt is a SINGLE-USE token and its consumption is what `finidem` (`ld8lb3`) had to work around when two actors each tried to spend it. Here a preview spends it. An operator (or a driver) that previews to decide whether to apply has already applied, and the message it gets back says `finalized`, not `would finalize`, so the only signal that something irreversible happened is that wording. Note HEAD is NOT silently wrong about the outcome: it does report `finalized`. The defect is that a no-`--apply` invocation can reach that state at all.

WHY IT IS NARROW, stated so nobody over-prioritizes it. It requires a previously interrupted finalize that reached `committed-incomplete`, which means the lifecycle commit was ALREADY made by the earlier attempt. So the resume is not fabricating a transition; it is completing one that demonstrably happened, and the post-commit resume is deliberately "RESUMED, never reverted". The bug is the CONTRACT VIOLATION on the preview surface, not a fabricated success.

WHAT A FIX MIGHT LOOK LIKE (not decided here): have `_early_recovery_result` take the `apply` flag and, when false, REPORT the recoverable state and the command that would complete it rather than performing it; or move the `apply` test ahead of early recovery; or make the resume path refuse without `--apply` and name the exact re-invocation. Each changes what a preview promises about recovery, so it is a design question.

WHERE: `agent_workflows/ipd_lifecycle.finalize` (early recovery runs before the `if not apply:` arm), via `agent_workflows/ipd_lifecycle._early_recovery_result` and `_resume_post_commit`.
Evidence: the three transcripts above; the `--apply` help string "Perform the transition (default: preview the precheck)" in `cli.py`.
