- Id: 10qxm7
- Status: open
- Set: specconsent
- Priority: medium
- Work-Kind: feature
- Summary: Decide whether a run whose queue declares a spec edit must pause for explicit human acknowledgement before spawning anything

## Workflow history
- 2026-09-08 created (aw backlog): RAISED BY THE MAINTAINER 2026-09-08 while resolving st5klo (specvis-01) OQ-01 and explicitly deferred: 'I think we might need a backlog for the pause and assert. That one is worth further discussion later.' st5klo makes the spec-edit announcement real on both hosts and at both ends of a run, but it is REPORT-ONLY BY DESIGN ('changes what the operator is TOLD, never what a run is ALLOWED to do'), so an unattended run that will rewrite a spec still prints a warning and proceeds with nobody consenting. Filed as a DECISION item, not a build item: the hard question is what the UNATTENDED answer is, since an acknowledgement prompt is TTY-shaped and --full-auto exists to avoid exactly that, and an override flag risks becoming reflexive (the failure mode gjadwm records). Four questions recorded in the body. st5klo should land first because a consent gate needs a reliable host-neutral answer to 'which specs will this queue edit?' and today only one host announces at all. No Blocks-Release: this is a strengthening of a control whose reporting half is already gated.

/tmp/opencode/pausebody.md
