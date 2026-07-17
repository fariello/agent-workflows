# Provenance and cross-validation

This package is human-owned and AI-assisted. This document is deliberately explicit about how the analysis was produced, so the maintainers can weigh it accordingly. We are not presenting AI output as independent unaided human work; we are offering thorough, cross-reviewed assisted analysis to support a human-owned report, and we are asking permission to do so.

## How the analysis was produced

1. Black-box runtime testing on a controlled multi-user Linux host with two real accounts (victim/attacker), plus corroboration by HPC/research-computing colleagues on their own controlled Slurm environments. See 02. Testers are deliberately not individually attributed because we cannot precisely reconstruct who ran which subset; treat colleague-reported items as independently corroborated but not all re-run by the primary reporter.
2. Source validation against the OpenCode tree (a downstream fork's `dev` at `08fb47373`), producing file:line citations. See 03.
3. Iterative drafting of an advisory, then adversarial review by three independent AI agents, then correction. See below.
4. A human (the reporter) reviews, verifies, and owns the final submission and every material claim.

## Three-agent adversarial cross-validation

The findings were challenged and corrected by three independent agents, each with a different vantage point. This is why we have reasonable confidence in the load-bearing claims and, equally important, why several early over-claims were caught and removed.

- Agent 1 - "opencode" (source-grounded): had the OpenCode source tree. Validated the advisory against source, supplied the file:line citations, and confirmed the central chain. It also authored initial patch sketches.
- Agent 2 - "agent-workflows" (same site): ran the controlled two-account runtime campaign, assembled the advisory, and reconciled runtime observations with source. It performed the black-box discovery/reach/disclosure/exec/mitigation tests.
- Agent 3 - off-site third-party (independent model/vantage): performed an independent review of the findings and the patch sketches, and produced a corrected patch proposal.

Each treated the others' output as untrusted and re-verified load-bearing claims rather than deferring.

## What the cross-review caught and corrected (evidence of rigor)

Framing corrections applied to the findings (an earlier draft was wrong on these; the corrected versions are what appears in 01-03):
- Filesystem: reframed from "no confinement / traversal bug" to "caller-selected confinement root" after source review showed the `contains` guard is present and correct; the exposure is the caller-supplied `directory`.
- Permission: split `/shell` (ungated) from `/message` (permission-gated, blocks on `ask`); the earlier blanket "API tool calls are ungated" was corrected to apply only to `/shell`.
- `--mdns`: narrowed to "only when no explicit hostname is set."
- Fail-open warning: corrected from stderr to stdout.
- Stealth: bounded to "attacker-created new session is stealthy"; injection into an ACTIVE attended session was observed VISIBLE and is not claimed as stealth.

Patch defects caught by the independent third-party review (and conceded by the patch author):
- A `serve.ts`-only startup fix would miss `web.ts`, which starts a listener independently (both must share one startup policy).
- A naive `permission.ask` inserted into the shell path would sit inside an uninterruptible region without `restore(...)`, making the approval wait non-interruptible (cannot be cleaned up on cancel/shutdown).
- A naive gate would hang indefinitely on a headless/bare server with no approval responder; headless behavior must be deterministic (fail fast unless pre-approved).
- Using the raw command as the remembered `always` pattern and using `Effect.orDie` for expected denials were both wrong; a shared normalized shell-permission planner is the correct approach.
- A finite secret-name blacklist is structurally incomplete because provider options/headers are extensible; a schema-defined public projection is the honest fix.

The result of that adversarial process is the sequenced PR A-E design in 04, which supersedes the initial patch sketches.

## Honest limits

- Source line numbers are from a fork's `dev` at `08fb47373`; re-pin to the target upstream release before any fix.
- The patches (04) are design/pseudodiff, not compiled or tested; some illustrative method names must be validated against the real tree.
- Not every test was re-run by the primary reporter; some were corroborated by colleagues on separate HPC environments.
- The `SessionPrompt.command` / config-markdown shell path is only partially traced; it must be resolved before any claim that the command-execution surface is fully closed.
- We did not run the cross-user attack on any production host carrying real users; the production observation in 02 is same-user plus launch-path inspection only.

## Why we are asking rather than submitting

The project's SECURITY.md states that AI-generated security reports are not accepted and may result in a ban, that server access when opted-in is expected behavior, and that the permission system is not a security sandbox. We take all three seriously. We are asking permission to submit this AI-assisted, human-owned, cross-reviewed material because the shared-infrastructure blast radius seems worth a conversation, and because the contained changes in 04 look able to reduce risk while preserving legitimate server/IPC use. If the maintainers prefer, we will instead provide a concise human-authored report with this analysis as supplemental material, or we will treat the whole matter as out of scope and keep it internal. We defer to them on scope, format, and disclosure timeline.
