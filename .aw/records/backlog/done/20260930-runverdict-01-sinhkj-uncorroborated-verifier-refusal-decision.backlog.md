- Id: sinhkj
- Status: done
- Graduated-To: runverdict
- Set: runverdict
- Priority: medium
- Work-Kind: followup
- Summary: Decide whether an uncorroborated verifier turn (claimed tests_run unmatched by its own session log) should ever refuse integration

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD q4uifc executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-runverdict-11-q4uifc-decide-that-an-uncorroborated-verifier-turn-never-refuses-in.ipd.md); evidence .aw/records/plans/executed/20261002-runverdict-11-q4uifc-decide-that-an-uncorroborated-verifier-turn-never-refuses-in.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: q4uifc
- 2026-09-30 created (aw backlog): Filed as the durable carrier for the refusal question plans bjx20r and btak7a deliberately do not decide

FILED as the durable carrier for a decision two pending plans (`bjx20r` Order 08, `btak7a` Order 09, both from backlog `5xgllt`) deliberately DO NOT make, so the question survives their execution instead of vanishing when they class `done`.

THE QUESTION. Those two plans make it computable whether a verifier's claimed `tests_run` commands are corroborated by the tool calls its own verifier-turn session log shows it made, and they RECORD and RENDER the three-state answer (`corroborated` / `uncorroborated` / `indeterminate`). Neither refuses, downgrades, or changes any disposition on it. So after both execute, a verifier that writes a plausible command string having run nothing is still recorded `verified` and its lane still integrates; the only change is that the discrepancy is now VISIBLE. Should it eventually BLOCK integration?

THE CASE AGAINST REFUSING, which is why the plans do not. The maintainer ruled twice (2026-09-08 and 2026-09-20, recorded in spec `25kzda` Section 5.1 and restated with four reasons in `runner_shared`'s pre-work-suite-baseline comment block) that no programmatic gate may refuse a verdict on derived suspicion of dishonesty: "You cannot build a pre-test that detects deception ... We're mitigating sloppiness, not malice." Reason 3 of that block applies to a corroboration module verbatim: a genuinely malicious agent has write access to the file and would rewrite the gate. Separately, plan `bjx20r`'s F-5 measures FOUR mechanisms by which a GENUINE test run is invisible or unmatchable (subagent delegation, which emits nothing into the parent session log; `make test` indirection; command chaining; and claim truncation at 120 characters or prose wrapping), so an `uncorroborated` verdict is not yet trustworthy enough to strand a verified lane on.

THE CASE FOR. Spec `25kzda` Section 5.1 already declares a verifier's self-report INADMISSIBLE as completion evidence ("an agent-authored summary or checklist without captured evidence", "a verifier's opinion") while declaring captured tool events ADMISSIBLE ("hash-bound argv-list tool events with exit codes and captured-output digests"), and Section 4.2 closes that captured tool events are admissible "because they are structured, hash-bound repository evidence, not agent narration". Refusing on a contradiction between the two arguably enforces a rule the spec already states.

WHAT WOULD MAKE IT DECIDABLE: an observed false-positive rate for `uncorroborated` over real runs. Plan `bjx20r`'s E-06 measures it, but `.aw/records/runs/` is gitignored and absent from every lane worktree, so a lane-executed run will produce a zero-row table and the real-corpus calibration will still be outstanding. The honest sequencing is therefore: ship the record (both plans), accumulate verdicts across real runs, then revisit this item with the observed rate in hand.

IF THE ANSWER IS YES, it is a NEW plan consuming the field `btak7a` adds, and it would OWE a spec `25kzda` amendment, because it changes the authority under which a verified verdict may be recorded.
