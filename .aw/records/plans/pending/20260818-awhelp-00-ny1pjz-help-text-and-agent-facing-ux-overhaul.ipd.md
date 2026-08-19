# IPD: help text and agent-facing UX overhaul

- Date: 2026-08-18
- Kind: orchestrator
- Concern: The `aw` CLI help is written for the maintainer who already knows the system, not for the two audiences that actually read it: a layperson learning the tool and a coding agent deciding how/when/why to invoke a verb. Help strings are terse or jargon-laden ("Validate the backlog tree; fail closed.", "Owner verbs for AW project identity and the AW_HOME registry..."), the whole `aw storage` help is opaque start-to-finish, `--phase PHASE` is a bare free-form string with no explanation of its five meaningful values, arg-hungry verbs (`ipd`/`show`/`storage`) give unhelpful missing-argument output with no examples, `aw --help` is a single sentence with no epilog and behaves identically whether or not it is a TTY (so an agent piping `--help` gets nothing to reason with), and several read verbs lack `--json` machine output / documented exit codes. Addresses TODO items 4, 10, 13, 14, 29, 31 plus a `--json`/exit-code consistency addition.
- Scope: The CLI help surface only (agent_workflows/cli.py: the per-verb `help=`/`description=` at add_parser, the `_DESCRIPTIONS` dict at cli.py:36-323 applied by `_apply_descriptions` at cli.py:326-344, the top-level parser at cli.py:378-383, and the `--phase` arg at cli.py:698-702) plus read-verb output plumbing where `--json`/exit codes are missing. IN: rewriting terse/jargon help strings for clarity to both a layperson and an agent; expanding `--phase` help to name and explain each phase (author|review-finalize|pre-execution|pre-transition|post-transition, semantics from ipd_lint.py:589-669); a verbose non-TTY `aw --help` (epilog + when/why guidance for agents); richer missing-arg/`--help` output with examples for `ipd`/`show`/`storage`; adding `--json` to read verbs that lack it + documenting exit codes (0/1/2) uniformly. OUT: the command GRAMMAR redesign (Set awcmdsurf), color/pretty output (Set awcolor), the `check` engine internals (Set awcheck), and any behavior change beyond help text + read-verb output shape. This Set is text-and-output-shape only; it does not move verbs or change their actions.
- Status: reviewed
- Set: awhelp
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ny1pjz

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): high-level skeleton from TODO items 4,10,13,14,29,31 + --json/exit-code consistency; children to be fleshed out.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Orchestrator for help/UX; verified _DESCRIPTIONS:36 / _apply_descriptions:326 / --phase:699 anchors; child decomposition sound; text/output-shape changes only; no findings.

## Goal

Make every `aw` help affordance legible to both a first-time human and a coding agent: rewrite terse/jargon help
strings, explain what `--phase` actually means, give arg-hungry verbs helpful missing-arg output with examples,
make `aw --help` verbose and self-explaining when piped to a non-TTY agent, and give read verbs consistent
`--json` output and documented exit codes. Split into three cohesive child IPDs (string rewrites, agent-facing
verbose help, machine output/exit codes) so each is independently reviewable and testable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..03 through the IPD lifecycle (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing. On completion, confirm every rewritten help string, the verbose non-TTY `aw --help`, the arg-hungry-verb examples, and the `--json`/exit-code consistency all land, and that no behavior beyond help text + read-verb output shape changed.
  - Depends on: none
  - Expected outcome: Orders 01..03 executed; all terse/jargon help rewritten; `--phase` explained; `aw --help` verbose for non-TTY agents; `ipd`/`show`/`storage` give helpful missing-arg output with examples; read verbs honor `--json` + documented exit codes; full suite green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Split by concern so each child is independently reviewable and testable (string content, agent-facing verbosity, machine output):

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | (to scaffold) awhelp-descriptions-rewrite | Rewrite every terse/jargon `help=`/`description=` string and `_DESCRIPTIONS` entry so it is clear to a layperson AND a coding agent: backlog `check` (cli.py:1481), the whole `storage` family (cli.py:179-214), `project` (cli.py:162-166), and the `ipd`/`show`/`todo`/action verbs. Expand the `--phase` help (cli.py:698-702) to name and explain each phase (author/review-finalize = structural; pre-execution = no blocking OQ; pre-transition = all E performed + V pass + evidence; post-transition = executed needs history line), sourced from ipd_lint.py:589-669. Note `_apply_descriptions` (cli.py:326-344) OVERWRITES inline `description=` for backlog subverbs, so canonical text belongs in `_DESCRIPTIONS`. + tests asserting the new strings render. | none |
| 02 | (to scaffold) awhelp-agent-verbose | Make `aw --help` verbose for a non-TTY reader: add an epilog to the top-level parser (cli.py:378-383) with when/why guidance for coding agents (what `aw` is for, when to reach for it, how the record lifecycle fits), rendered richly when stdout is not a TTY. Give the arg-hungry verbs (`ipd`, `show`, `storage`) helpful missing-argument and `--help` output with concrete usage examples instead of a bare argparse error. + tests capturing non-TTY help + missing-arg output. | 01 (consumes the rewritten strings) |
| 03 | (to scaffold) awhelp-json-and-exitcodes | Add `--json` machine output to read verbs that lack it (bringing them in line with `attention --format json` at attention.py:362 and existing `--agent` flags) and document exit codes (0 = ok, 1 = failure/nonconforming, 2 = usage error) uniformly across read verbs, surfaced in the rewritten help. + tests asserting `--json` shape + exit codes. | 01 |

## Completion criteria (the whole Set is done only when)

- Orders 01..03 executed and moved to `.aw/records/plans/executed/`.
- No terse/jargon help string survives: backlog `check`, the `storage` family, `project`, and the `ipd`/`show`/`todo`/action verbs read clearly to both a layperson and an agent; a spot review of `_DESCRIPTIONS` finds no unexplained jargon.
- `aw ipd lint --phase` help enumerates and explains all five phase values.
- `aw --help` piped to a non-TTY prints the verbose epilog with agent when/why guidance; `ipd`/`show`/`storage` invoked without required args (and with `--help`) print usage examples.
- Every read verb that emits a report honors `--json` and returns documented exit codes (0/1/2), consistent with `attention --format json`.
- Full serial suite green; `aw sanitize --agent` clean; no behavior beyond help text + read-verb output shape changed.

## Cross-IPD validation

- Orders 02 and 03 both consume the canonical strings produced by Order 01; run Order 01 first so the epilog/verbose help and the `--json`-surfaced exit-code docs quote the final wording (no drift between `_DESCRIPTIONS` and the epilog).
- After all three Orders land, re-run the full suite and diff the help output to confirm the changes are additive (text + output shape) and no verb's ACTION changed.
- Coordinate with Set awcmdsurf (grammar) and awcolor (pretty output): this Set touches only help text/output shape, so it must not conflict with a grammar rename or a color layer landing in the same files; rebase help edits onto whichever lands first.

## Deferred / out of scope (with reason)

- Command grammar / verb renames: Set awcmdsurf owns the noun-verb redesign; this Set only rewrites the help of the verbs as they currently stand.
- Color / 256-color pretty output: Set awcolor.
- The `check` engine internals and any validation-logic change: Set awcheck; here `--phase` help is documentation-only.
- Any change to a verb's action or arguments beyond adding `--json` to read verbs; this Set is text-and-output-shape only.

## Scope check

- Over-scope: none - every child maps to a listed TODO item (4, 10, 13, 14, 29, 31) or the `--json`/exit-code consistency addition; grammar/color/engine internals are explicitly delegated to other Sets.
- Under-scope: none - the three Orders cover the string rewrites (incl. `--phase`), the agent-facing verbose/non-TTY help + arg-hungry-verb examples, and the machine-output/exit-code consistency, which is the full span of the concern.

## Required tests / validation

Per-Order V-items plus the whole-Set completion criteria. E-01's verification renders `aw --help` (TTY and
non-TTY), `aw ipd lint --help`, `aw storage`/`aw ipd`/`aw show` with missing args, and a `--json` read-verb
invocation, pastes the output, and re-runs the full serial suite after all Orders land.

## Open questions

### OQ-01: How verbose should the non-TTY `aw --help` epilog be for agents?

- Blocking: no
- Status: open
- Owner: maintainer (resolve at Order 02)
- Resolution or deferral rationale: Recommendation - a compact epilog (what `aw` is, the record-lifecycle mental model, and a "when to reach for which verb" pointer), not an inlined manual. Non-blocking; length is tunable at Order 02 without affecting the other Orders.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all three child Orders show `Status: executed` under `.aw/records/plans/executed/`; paste (a) the rewritten backlog `check`/`storage`/`project`/`ipd`/`show` help proving the terse/jargon strings are gone, (b) `aw ipd lint --help` showing all five `--phase` values explained, (c) `aw --help` piped to a non-TTY showing the verbose agent epilog, (d) `aw storage`/`aw ipd`/`aw show` run with missing args showing usage examples, (e) a `--json` read-verb invocation with its documented exit code; plus the full serial suite tail and `aw sanitize --agent` clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: three Orders for one coherent objective (a legible help surface for humans and agents), split by concern - string content (01), agent-facing verbosity + arg-hungry-verb examples (02), machine output + exit codes (03) - so each is independently reviewable and testable while 02/03 build on 01's canonical strings.

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The orchestrator
(opencode Opus 4.8) drives each child Order through its own lifecycle, OWNS all verification + path-scoped
commits (`git commit -m msg -- <path>`, never `git add -A`, never push), and moves each Order (and finally this
orchestrator) to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and the
V-items are verified with pasted evidence. Large mechanical Orders may be handed to Gemini via `agy` (blocking),
but the orchestrator OWNS verification and commits and never trusts a report on faith.
