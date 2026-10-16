- Id: 7rs77x
- Status: open
- Set: uypgvi
- Priority: low
- Work-Kind: followup
- Summary: release_readiness: artifact_manifest fails on a dev-checkout install because index.md WORKFLOWS-VERSION stamp differs from the resolved VERSION

## Workflow history
- 2026-10-16 created (aw backlog): release_readiness: artifact_manifest fails on a dev-checkout install because index.md WORKFLOWS-VERSION stamp differs from the resolved VERSION

Measured 2026-10-16 at cb349046d by plan 4bw2u5 (OQ-02): installing a managed repo from a development checkout writes .aw/system/VERSION = 1.3.0rc2.dev10960+gcb349046d (engine resolves VERSION) while the installed index.md keeps WORKFLOWS-VERSION 1.2.1, so gate_artifact_manifest FAILS with 'version stamp mismatch'. Not an absent input. May not occur for a tagged release install (RELEASING.md bakes VERSION before tagging); confirm on a release install and decide whether the gate or the installer should reconcile. Classify as bug if it reproduces on a released install.
