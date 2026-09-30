- Id: hv8zlg
- Status: graduated
- Graduated-To: hv8zlg
- Set: hv8zlg
- Priority: low
- Work-Kind: chore
- Summary: A stranded-lane drift detail can exceed the Section 8.8 descriptive-field bound and nothing checks it

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: mc6r92
- 2026-09-28 created (aw backlog): A stranded-lane drift detail can exceed the Section 8.8 descriptive-field bound and nothing checks it

FILED AS THE CARRIER for the deferred row in plan `8njbv5` (strandwt-01), which measured this while authoring an unrelated wording change and declined to fix it in scope.

MEASURED 2026-09-28 in a lane at HEAD `9514ff02`, against the run records resolved through `attention._resolve_runs_repo_root` (the main checkout, 300 run dirs):

`attention.stranded_lane_drift(Path("."))` returns ONE row today, `aw/lane/8l8dgb` / `attention.lane-superseded` / severity `info`. Its `detail` is 414 characters against `attention_contract.MAX_DESCRIPTIVE_LEN` of 300, and `attention_contract.is_safe_descriptive(detail)` returns False.

WHY IT IS NOT CAUGHT: `attention.stranded_lane_drift` never calls `is_safe_descriptive`. That predicate's only callers are in `specs`, `backlog` and `check_engine`, so the bound spec Section 8.8 states ("Every descriptive field is a single logical line with a defined maximum length ... Over-length values are a contract violation, not silently truncated") is simply not applied to a lane detail. Simulated over all 519 lane records, lengths run 164 to 414 with a median of 194, so exactly one row is over today and the shape is near the bound rather than far from it.

THE FIX IS A CONTRACT DECISION, NOT A ONE-LINER, which is why it was deferred rather than folded in. Both obvious routes are choices about the output-safety contract: truncating the field is what Section 8.8 explicitly forbids ("not silently truncated"), and emitting a new `attention.unsafe-field` violation would add a second finding for a lane the gate ALREADY reports, changing what `--check` prints for a row that is otherwise correct. A third option is to shorten what the assembly puts in the field (the `why` text and the remedy hint are the long parts), which changes no contract but does change output operators read.

NOT A REGRESSION CAUSED BY `8njbv5`: that plan's marker adds 21 characters to rows whose worktree is ABSENT, and this row's worktree EXISTS, so it gains nothing. Measured with the marker simulated, the 514 rows that would gain it run 185 to 223 characters, all inside the bound with 77 characters of headroom at the maximum.
