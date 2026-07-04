# IPD: Guided "walk me through using agent-workflows" onboarding workflow

- Date: 2026-07-04
- Concern: usability / adoption - a first-time user needs an in-agent, guided
  introduction to the toolkit, not just a README to read.
- Scope: one new guided workflow (wizard style, like setup-repo). No change to existing
  workflow behavior.
- Status: PENDING (proposal for human approval; not executed)

## Goal

Give a newcomer a guided, in-agent tour of the toolkit: what it is, what the workflows
do, when to use which, and how to run them in the user's specific tool - interactively,
adapting to this repo's state and the user's goal. The in-agent complement to the README
on-ramp.

## Why

- The README is a good written on-ramp, but a first-time user in an agent still has to
  read it and map it to their situation. A guided tour meets them where they are: "what
  are you trying to do?" -> point them at the right workflow and run it with them.
- Lowers adoption friction, which is the difference between a toolkit that gets used and
  one that gets installed and forgotten.
- Fits the proven guided-wizard pattern (setup-repo, scaffold).

## Proposed design

An `onboarding` / `tour` / `getting-started` workflow that:
1. **Detects context:** is the toolkit freshly installed? Has `setup-repo` been run? Is
   there a plan lifecycle? What is the repo type? Tailors the tour accordingly.
2. **Explains the mental model briefly:** the plan -> build -> review -> ship spine; the
   difference between review (assess/release-review), plan-time (plan-review), and
   guided (setup-repo/scaffold) workflows; where IPDs and run records live.
3. **Asks the user's goal** and routes: "set the repo up" -> setup-repo; "check one
   thing" -> assess <thing>; "review a plan" -> plan-review; "review before shipping" ->
   release-review; "add a workflow" -> scaffold. Offers to run the chosen one.
4. **Shows how to run things in THIS tool:** native `/command` (OpenCode/Claude Code) vs.
   read-and-execute (Codex/Cursor/Antigravity/others), using the per-tool guidance.
5. **Points to the catalog** (`/list`, the toolkit-discovery IPD) and the README/DECISIONS for depth.
6. Read-only/explanatory by default; only runs another workflow with the user's say-so.
   Safe to run any time.

## Scope check

- Over-scope: do not duplicate the README or the `/list` catalog - the tour ORCHESTRATES
  and ROUTES; it references the catalog (the toolkit-discovery IPD) for the full list rather than
  re-enumerating it. Keep it a guide, not a second source of truth.
- Under-scope: it must actually adapt to context and goal, not just recite the README;
  otherwise it adds nothing over reading the README.

## Dependencies / sequencing

- Best after the toolkit-discovery IPD (`/list` catalog) so the tour can point at a live catalog, and after
  the command-surface-redesign IPD (parameterized commands) so it teaches the final command surface. Could be built
  earlier and updated, but the content depends on the command surface being settled.

## Required validation

- Running it on a fresh install walks a newcomer to a sensible first action (usually
  setup-repo); on an already-set-up repo it routes to review/assess instead.
- Tool-specific run instructions are correct; it never runs a workflow without consent.

## Open questions

1. Command name: `onboarding`, `tour`, `getting-started`, or `start`? (`start` is short
   and inviting; `tour` is clear.)
2. Build it before or after the command surface settles (the command-surface-redesign IPD/2)? Content depends on
   the final surface, so likely after - or build now and revise when the command-surface-redesign IPD/2 land.
3. Overlap with setup-repo: the tour ROUTES to setup-repo; keep them distinct (tour =
   orient + route; setup-repo = do the setup).

## Approval and execution gate

Proposal only. Best sequenced after the command surface (the command-surface-redesign IPD) and catalog (the toolkit-discovery IPD) are
settled, since it teaches them. Approve/reorder before execution.
