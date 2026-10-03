- Id: ku8szz
- Status: done
- Graduated-To: ku8szz
- Set: ku8szz
- Priority: low
- Work-Kind: chore
- Summary: Decide whether a deterministic author-time rule can refuse a bare comparison against a retired status token without firing on the six unrelated vocabularies that share the spellings blocked and partial

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD fr19jr executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-ku8szz-01-fr19jr-refuse-a-dead-legacy-status-comparison-at-author-time-scoped.ipd.md); evidence .aw/records/plans/executed/20261002-ku8szz-01-fr19jr-refuse-a-dead-legacy-status-comparison-at-author-time-scoped.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: fr19jr
- 2026-09-30 created (aw backlog): Decide whether a deterministic author-time rule can refuse a bare comparison against a retired status token without firing on the six unrelated vocabularies that share the spellings blocked and partial

DEFERRED BY PLAN `qvfd4l` (from backlog `cxrpwv`), which carries the behavioral fence but not this checker.

Plan `qvfd4l` sweeps every reader that compares a queue-item status against a key of `runner_shared.TERMINAL_STATUS_ALIASES`, fixes the three surfaces whose operator-visible behavior was measurably wrong, and pins all three behaviorally off the alias table so a future rename fails a test. What it deliberately does NOT do is refuse a NEW dead comparison at author time.

THE DESIGN PROBLEM IS WHY IT IS DEFERRED RATHER THAN SIMPLY UNDONE. A rule keyed on the token text alone would fire on at least six vocabularies that legitimately contain `blocked` or `partial` and are NOT runner terminal statuses: backlog item status (paired with `Gate-Kind`/`Gate-Ref`), IPD execution and validation state (`ipd_schema.EXEC_STATES`, `VALIDATION_RESULTS`), release status (`releases.RELEASE_STATUSES`), verifier verdict (`verify_roles.RESULT_PARTIAL`, `runner_shared.VERIFY_DISP_BLOCKED`), research pipeline position (`research_contract.PIPELINE_POSITIONS`), and the attention class vocabulary. Measured while authoring `qvfd4l`: an AST sweep of `agent_workflows/` found 258 legacy-token literals across 34 modules, of which 15 were bare equality comparisons and ALL 15 belonged to one of those other vocabularies. So a naive rule would be almost entirely false positives.

WHAT WOULD MAKE IT TRACTABLE is type information the token does not carry: the rule needs to know that a given comparison's left-hand side is a RUN QUEUE ITEM status rather than a backlog gate state. Options worth measuring include keying on the enclosing module's membership in a runner/renderer allowlist, on the variable or subscript name (`item.get("status")` in a run-record context), or on proximity to an already-canonicalizing call. None has been measured.

SEQUENCING: wait until `qvfd4l`'s behavioral fence has been in place long enough to show whether it is sufficient on its own. If no further dead reader appears, this is not worth building; if one does, that instance supplies the evidence for the rule's shape. No measured defect rests on this item's absence today.
