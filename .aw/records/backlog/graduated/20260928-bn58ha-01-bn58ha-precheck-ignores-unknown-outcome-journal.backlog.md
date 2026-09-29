- Id: bn58ha
- Status: graduated
- Graduated-To: bn58ha
- Blocks-Release: next
- Set: bn58ha
- Priority: medium
- Work-Kind: bug
- Summary: finalize_precheck reports 'precheck passed' for a plan whose finalize is wedged by an unknown-outcome journal, so the preview surface contradicts what --apply will do

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: hlv737
- 2026-09-28 created (aw backlog): Filed while authoring cnf7gw's graduation plan; measured, see body.

MEASURED 2026-09-28 at HEAD 6171375d, in the scratch harness `/tmp` reproduction described below.

WHAT IS WRONG. `ipd_lifecycle.finalize_precheck` validates the begin receipt, runs pre-transition lint and computes the scope delta, and it does NOT read the finalize transaction journal at all. So when a prior attempt left `PHASE_UNKNOWN_OUTCOME` (which the contended fast-forward arm does; see `cnf7gw`), the preview surface reports exit 0 `precheck passed (receipt valid, pre-transition conforming; scope delta computed)` while `--apply` returns exit 2 `finalize journal for <id> is in unknown-outcome (ambiguous prior attempt)`. An operator or driver that previews before applying is told GO by the very surface whose job is to predict the apply.

MEASURED, same fixture, immediately after a contended refusal wedged the journal:
- `finalize_precheck(root, plan)` -> `(0, 'precheck passed (receipt valid, pre-transition conforming; scope delta computed).', findings=())`
- `finalize(root, plan, ..., apply=False)` -> exit 2, 'finalize journal for abc123 is in unknown-outcome'

So `finalize` itself DOES see it (the journal check lives in `_finalize_transaction`'s resume arm, reached on both the preview and apply paths through `finalize`), and only the `finalize_precheck` function is blind. That asymmetry is the defect: two functions that both claim to answer 'may this finalize proceed' disagree.

WHY IT IS NARROW, stated so nobody over-prioritizes it. `finalize(apply=False)` does report it, and that is the surface `aw ipd finalize` without `--apply` actually uses, so an operator running the CLI is not misled today. The exposure is to any caller that uses `finalize_precheck` DIRECTLY as a go/no-go oracle.

WHERE: `agent_workflows/ipd_lifecycle.finalize_precheck`.
Evidence: the two-call reproduction above; the journal resume arm is `_finalize_transaction`'s `existing is not None` block.
