- Id: 10qxm7
- Status: done
- Graduated-To: specpause
- Set: specconsent
- Priority: medium
- Work-Kind: feature
- Summary: Decide whether a run whose queue declares a spec edit must pause for explicit human acknowledgement before spawning anything

## Workflow history
- 2026-09-25 set (aw backlog): closed by aw oc run: IPD 1g4i1t executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260924-specpause-01-1g4i1t-pause-for-explicit-acknowledgement-before-a-run-that-declare.ipd.md); evidence .aw/records/plans/executed/20260924-specpause-01-1g4i1t-pause-for-explicit-acknowledgement-before-a-run-that-declare.ipd.md
- 2026-09-25 graduated (aw set): graduated into specpause plan 1g4i1t (to-review); decision resolved in the plan's OQ-01
- 2026-09-08 created (aw backlog): RAISED BY THE MAINTAINER 2026-09-08 while resolving st5klo (specvis-01) OQ-01 and explicitly deferred: 'I think we might need a backlog for the pause and assert. That one is worth further discussion later.' st5klo makes the spec-edit announcement real on both hosts and at both ends of a run, but it is REPORT-ONLY BY DESIGN ('changes what the operator is TOLD, never what a run is ALLOWED to do'), so an unattended run that will rewrite a spec still prints a warning and proceeds with nobody consenting. Filed as a DECISION item, not a build item: the hard question is what the UNATTENDED answer is, since an acknowledgement prompt is TTY-shaped and --full-auto exists to avoid exactly that, and an override flag risks becoming reflexive (the failure mode gjadwm records). Four questions recorded in the body. st5klo should land first because a consent gate needs a reliable host-neutral answer to 'which specs will this queue edit?' and today only one host announces at all. No Blocks-Release: this is a strengthening of a control whose reporting half is already gated.

/tmp/opencode/pausebody.md
