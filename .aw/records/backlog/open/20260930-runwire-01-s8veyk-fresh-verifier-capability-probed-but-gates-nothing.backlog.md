- Id: s8veyk
- Status: open
- Set: runwire
- Priority: medium
- Work-Kind: chore
- Summary: supports_fresh_verifier_session is probed but gates nothing: ACTION_CAPABILITY_REQUIREMENTS has one row and it requires no capability

## Workflow history
- 2026-09-30 created (aw backlog): Filed while authoring Set runwire from backlog ildjse. Sibling plan eow7p4 enforces verifier session independence at the runner, but deliberately does NOT add a capability requirement row, because that would refuse whole action classes on a host and is a policy change with a much larger blast radius. This item carries that residual.

MEASURED at 2026-09-30 (lane worktree ildjse, HEAD cedab274).

WHAT EXISTS. host_sandbox_profile defines CAP_FRESH_VERIFIER_SESSION = 'supports_fresh_verifier_session' and the field on HostSandboxCapabilities. Its module docstring describes a STRICT probe: 'PROBED by attempt. The probe runs the real fresh-verifier contract twice and requires BOTH that distinct identities finalize AND that a reused identity is REFUSED, because a contract that never refuses enforces no separation while a caller believes verification was independent.'

WHAT IS MISSING. ACTION_CAPABILITY_REQUIREMENTS contains exactly ONE row, ACTION_READ_ONLY, whose required tuple is EMPTY, with the spec basis 'Nothing this contract represents is required, so a read-only action is never refused by this gate'. So no action requires supports_fresh_verifier_session, and the probe's verdict gates nothing. The probe runs, produces a correct verdict, and no caller consults it for any mutating action.

WHY THAT MATTERS, in the module's own words. The docstring's justification for probing strictly is that otherwise 'a caller believes verification was independent' while nothing enforces separation. That sentence describes the CURRENT state of the action preflight: the capability is measured and then not required.

THE HONEST LIMIT ON SEVERITY AND SCOPE. This is filed chore, not bug. No incorrect output is produced: the probe is right and the preflight simply asks nothing of it. And the fix is NOT merely adding a row: a required capability REFUSES an action class on a host whose probe failed, so the work is to decide WHICH action classes require WHICH runner-safety guarantees (spec 25kzda 5.2's action table is the stated basis for these rows), and to establish that hosts in real use actually pass the probe, or the row turns a working configuration into a refused one. UnknownActionError already exists precisely so an unknown action is not silently given the read-only policy.

RELATED. Plan eow7p4 (Set runwire, from backlog ildjse) enforces the session-independence guarantee at the runner's own verify site and records this item as its deferred residual in OQ-02; that enforcement is independent of this row and is valuable whether or not the row is ever added. Note also supports_commit_gateway, which is DECLARED AND NEVER PROBED by deliberate decision so it fails closed, and whose docstring forbids inferring support from a driver-side helper; that is a different and already-decided case, not part of this item.
