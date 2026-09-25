- Id: ibuxe6
- Status: open
- Set: ibuxe6
- Priority: low
- Work-Kind: followup
- Summary: three IPD-EXEC pre-transition finding codes are now trivially bindable and remain unbound names

## Workflow history
- 2026-09-20 created (aw backlog): Follow-up recorded by plan zzcrlo (finalback), whose spec-sync section required that a trivially-bindable code be RECORDED rather than scope-crept into that plan. Spec 25kzda Section 4.2//4.6 names 11 IPD-EXEC-* finding codes and all 11 grep to ZERO files, which the spec itself concedes at :39 while instructing at :106 to 'cite the shipped enforcers, not the codes, until the codes are bound'. zzcrlo followed that instruction. What it INCIDENTALLY established is that three of the eleven are now a one-to-one match for diagnostics `ipd_lint` already emits at its pre-transition checkpoint: IPD-EXEC-E-COMPLETE <-> "<E-id>: not 'performed' at pre-transition", IPD-EXEC-V-EVIDENCE <-> "<V-id>: not 'pass' at pre-transition" plus "<V-id>: empty Observed evidence at pre-transition", and IPD-EXEC-PRE-TRANSITION <-> the enclosing 'pre-transition gate did NOT conform' refusal. Binding those three would let the retryable-class allowlist key on CODES instead of prose (see backlog 144b3x) and would begin discharging the spec's own admitted gap. Binding the whole family is a larger project; these three are the cheap ones. WHERE: agent_workflows/ipd_lint.py C_CHECKPOINT//check_checkpoint, spec 20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md Section 4.6.
