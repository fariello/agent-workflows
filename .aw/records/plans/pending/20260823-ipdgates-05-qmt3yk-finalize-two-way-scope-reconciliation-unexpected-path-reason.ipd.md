# IPD: Finalize two-way scope reconciliation (unexpected-path reason, in-scope-unmodified acknowledgment)

- Date: 2026-08-23
- Kind: child
- Concern: `aw ipd finalize` (Order 04) computes the scope delta - files this execution changed vs the frozen `Scope-Paths` - but only REFUSES on an out-of-scope path. In real complex work, discovering mid-stream that you must touch an unforeseen file is common (often the rule), and agents are NOT trained to update `Scope-Paths` en route or even to run `aw ipd finalize` at all. A hard refusal on every unforeseen edit trains agents to treat the gate as noise (which then misses the real p7dqwz violation), and a refusal alone catches only EXTRA work, never MISSING work (a file declared in scope but silently never touched - the "went off the rails / didn't do what it said" failure). This IPD turns finalize's one-directional refusal into a low-friction, unskippable TWO-WAY reconciliation that SURFACES and ATTRIBUTES both deltas without relying on the agent to remember anything mid-stream. (DECISIONS.md D141.)
- Scope: Add the two-way scope reconciliation to `aw ipd finalize` (the finalize path from Order 04), with both an interactive batched prompt and a non-interactive `--scope-reason`/`--scope-ack` flag channel. Touch: the single-IPD lifecycle module (from Orders 03/04), agent_workflows/cli.py (the finalize prompt/flags + help), and tests/test_ipd_lifecycle_cli.py. Does NOT change how `aw ipd begin` freezes `Scope-Paths` (unchanged by human decision), does NOT alter the Order 04 refusal-vs-proceed decision beyond replacing bare refusal with reconciliation, does NOT build rollback (Order 06) or remove the bypass (Order 07), and (per /plan-review 2026-08-24) does NOT add an en-route `aw ipd scope add` convenience verb (dropped as over-scope: the reason is captured at finalize via `--scope-reason`, and the plan itself judged the en-route verb unreliable).
- Scope-Paths: grandfathered
- Status: approved
- Set: ipdgates
- Order: 5
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: qmt3yk
- Approval: 2026-08-24, human ("approved. go."): status set to approved

## Workflow history
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-24 reviewed (aw set): plan-review self-review (author); revisions applied - see workflow history
- 2026-08-24 /plan-review SELF-REVIEW (opencode its_direct/pt3-claude-opus-4.8-1m-us - NOTE: same agent that AUTHORED this plan; an independent reviewer is preferable): APPROVE WITH REVISIONS APPLIED. PR-001 (HIGH: the reconciliation was prompt-only, which would permanently lock autonomous/headless finalize of any plan with an unforeseen edit - added a non-interactive `--scope-reason <path>=<why>` / `--scope-ack <path>` channel + a fail-closed "names the exact command" headless-missing result, per the repo's status_set/run_gates convention); PR-002/PR-003 (human-resolved: DROPPED the en-route `aw ipd scope add` verb as over-scope/gold-plating - unreliable per the plan's own text, fully covered by `--scope-reason`, and needed an unspecified run-state store; removed E-02/V-02, renumbered E-03->E-02/V-03->V-02); PR-004 (made the in-scope-unmodified direction's dependency on the receipt's LITERAL declared Scope-Paths explicit). Verified Order 04 delivers the scope-delta computation this reuses. No blocking OQ.
- 2026-08-24 to-review (aw set): authored as new Order 05 (D141 finalize scope reconciliation); ready for review

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created - decomposed out of Order 04 at human direction (density: reconciliation is a distinct deliverable + test surface) and inserted as Order 05 (rollback -> 06, remove-bypass -> 07). Design per DECISIONS.md D141.

## Goal

Make `aw ipd finalize` reconcile the scope delta in BOTH directions at the one step that cannot be skipped (finalize is the chokepoint; Order 07 makes even `aw set executed` delegate into it). For files this execution CHANGED that are OUTSIDE the frozen `Scope-Paths`: require a short RECORDED REASON per file. For files declared IN `Scope-Paths` that were NOT modified: require a one-word ACKNOWLEDGMENT (e.g. "not-needed"). Both are collected in ONE batched, low-friction prompt (on a TTY) or supplied as `--scope-reason <path>=<why>` / `--scope-ack <path>` flags (headless), and written verbatim into the terminal `## Workflow history`/evidence so the deviation is permanently visible and attributable. The mechanism SURFACES and ATTRIBUTES deviations (defeating hiding, enabling later human/verifier review); it does NOT judge their legitimacy. finalize is the load-bearing, unskippable mechanism; there is deliberately NO separate en-route `scope add` verb (dropped at /plan-review as over-scope - the reason is captured at finalize, and an extra optional verb the plan judged agents would not reliably use is not worth a new command + store).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Two-way reconciliation at finalize

- [ ] E-01 In the single-IPD lifecycle module, extend `aw ipd finalize` so that, after computing the scope delta (reuse Order 04's exact computation - do not recompute differently), it reconciles BOTH directions: (a) each path this execution changed that is OUTSIDE `Scope-Paths` requires a non-empty REASON (this replaces Order 04's bare unexplained-path refusal for the LEGITIMATE case: reason given -> record + proceed; reason refused/empty -> do not finalize); (b) each path declared IN `Scope-Paths` but NOT modified requires a one-word ACKNOWLEDGMENT (default-acceptable answers like "not-needed" are valid and recorded - acknowledge-and-proceed, NOT a hard blocker). Write every answer verbatim into the terminal history/evidence. On a clean delta (nothing out-of-scope, nothing declared-but-unmodified) the reconciliation is a no-op and finalize proceeds silently.
  - Depends on: none
  - Note (INTERACTIVE and NON-INTERACTIVE channels are BOTH required - `aw ipd finalize` is routinely run by an agent in a non-TTY context, so a TTY-only prompt would permanently lock autonomous finalize of any plan with an unforeseen edit): on a TTY, present ONE batched prompt collecting all reasons/acks at once. Non-interactively, accept the answers as flags (e.g. `--scope-reason <path>=<why>` per out-of-scope path and `--scope-ack <path>[=<note>]` per declared-but-unmodified path), mirroring the repo's existing headless-mutation convention (`status_set.py:741-756`: agent mode returns a "confirmation/answers required" result naming the exact `next` command with the needed flags, and `--yes`/`run_gates` `needs_input` stop). A headless run with a non-empty delta and MISSING answers fails closed with a `needs_input`-style result that ENUMERATES each unanswered path and the exact `aw ipd finalize ... --scope-reason/--scope-ack ...` invocation to supply them - it does NOT hang on a prompt and does NOT silently skip.
  - Expected outcome: finalize confronts the agent/human with the full two-way delta at the unskippable step - via a batched prompt on a TTY or `--scope-reason`/`--scope-ack` flags headless; out-of-scope edits are recorded-with-reason, in-scope-unmodified are acknowledged, both land in the durable record; a clean delta is frictionless; a headless run missing answers fails closed naming the exact command to supply them (never hangs, never skips).
  - Execution state: pending

### Task group 2: Prove reconciliation + attribution + low friction

- [ ] E-02 Add `tests/test_ipd_lifecycle_cli.py` reconciliation tests: (out-of-scope, TTY) an execution that changed a path outside `Scope-Paths` prompts for a reason, records the given reason in the terminal history, and proceeds; refusing/empty reason does NOT finalize. (in-scope-unmodified, TTY) a declared-but-untouched path prompts for a one-word acknowledgment, records it, and proceeds. (both-at-once) a single batched prompt covers both directions. (clean) a fully in-scope, fully-covered execution shows no prompt and finalizes silently. (headless answered) the out-of-scope path answered via `--scope-reason <path>=<why>` and the declared-but-unmodified path via `--scope-ack <path>` both record and proceed. (headless missing) a non-empty delta with no flags fails closed naming each unanswered path + the exact `aw ipd finalize ... --scope-reason/--scope-ack ...` command. (attribution) the recorded reasons/acknowledgments are present verbatim in the terminal `## Workflow history`/evidence. Confirm `pytest -n auto` is green.
  - Depends on: E-01
  - Expected outcome: both delta directions, the batched single-prompt UX (TTY), the `--scope-reason`/`--scope-ack` headless channel, the clean no-op, the headless-missing fail-closed, and the durable attribution are all proven.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Order 04 (`v7e88a`) already computes the scope delta (diff base-HEAD..now restricted to `Scope-Paths`, per the path-overlap rule shared with Order 03) and currently REFUSES on an out-of-scope path; this IPD reuses that exact computation and replaces bare refusal with reconciliation for the legitimate case.
- `aw ipd begin` freezes `Scope-Paths` at start and is UNCHANGED by human decision; unforeseen mid-stream edits are handled by reconciliation at finalize, not by re-freezing.
- Finalize is the unskippable chokepoint: Order 07 makes `aw set executed` DELEGATE into finalize, so the reconciliation cannot be bypassed even by the "just mark it done" path.
- Agents are not trained to update scope en route or even to run finalize; the design therefore makes finalize the SINGLE load-bearing, mandatory, auto-computed mechanism (no separate optional verb that would be forgotten).
- The in-scope-UNMODIFIED direction (b) requires the receipt to carry the LITERAL declared `Scope-Paths` list (not just a digest), so finalize can compute "declared but not touched". This is the SAME receipt requirement Order 04 already flags (its precheck note: the receipt must persist the literal allowlist); this order depends on it. If the receipt carries only a digest, the in-scope-unmodified direction cannot run - STOP and report rather than skip it.

## Findings

The reconciliation's power is SURFACING + ATTRIBUTION, not judgment: a low-barrier "give a reason" field is trivially greenwashed ("n/a"), so the reason text alone does not prove legitimacy - but it makes the deviation impossible to HIDE, cheap to legitimately explain, and permanently ON THE RECORD for a human/verifier to weigh. Making finalize (not an en-route verb the agent will forget) the mandatory chokepoint is what guarantees the confrontation happens. The in-scope-unmodified direction is the only mechanism in the Set that catches MISSING work ("said it would touch X, didn't"); it is acknowledge-and-proceed because a declared-but-unneeded file is normal, not a failure. Out-of-scope edits carry slightly more weight (recorded reason) because they are the p7dqwz signature.

## Proposed changes (ordered, validatable)

1. Two-way reconciliation in finalize (interactive batched prompt + non-interactive `--scope-reason`/`--scope-ack` flags): out-of-scope -> recorded reason (proceed) / empty -> refuse; in-scope-unmodified -> one-word acknowledgment (proceed); clean delta -> silent; headless with delta + no answers -> fail closed naming the exact command (E-01).
2. Tests for both directions, batched TTY UX, headless flag channel, clean no-op, headless-missing fail-closed, durable attribution (E-02).

## Deferred / out of scope (with reason)

- The en-route `aw ipd scope add <plan> <path> --reason` convenience verb: DROPPED at /plan-review (2026-08-24, human) as over-scope/gold-plating - its only function (record the reason for an unforeseen edit) is fully served by finalize's `--scope-reason` flag, the plan itself judged agents would not reliably use it, and it needed an unspecified new run-state store. If a real need for capture-at-moment-of-realization emerges, file it as a separate follow-up.
- Changing how `aw ipd begin` freezes `Scope-Paths`: explicitly OUT (human decision - the frozen baseline stays; reconciliation absorbs mid-stream discovery).
- JUDGING whether a recorded reason is adequate: out of scope - that is human/verifier review reading the recorded reasons, not a linter.
- Rollback semantics (Order 06) and removing the raw bypass (Order 07): sibling orders.
- The `Scope-Paths` granularity/ergonomics debate (directory vs exact-file, narrowness expectations): a design tension recorded for Orders 02/03 (D141), not implemented here.

## Scope check

- Over-scope: none (the en-route `aw ipd scope add` verb was DROPPED at /plan-review as over-scope). Only the finalize reconciliation (interactive prompt + headless flags) + its tests.
- Under-scope: none for reconciliation; adequacy-judgment is deliberately human/verifier review, not this gate.

## Required tests / validation

- `tests/test_ipd_lifecycle_cli.py` reconciliation tests per E-02 (out-of-scope reason, in-scope-unmodified ack, batched TTY prompt, headless `--scope-reason`/`--scope-ack` channel, clean no-op, headless-missing fail-closed, durable attribution).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Amend the IPD lifecycle spec + `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` + CLI `--help` (via managed verbs) to document the finalize two-way reconciliation (interactive prompt + `--scope-reason`/`--scope-ack` headless flags) and the honest framing (surfaces + attributes, does not judge). Cite DECISIONS.md D141.

## Open questions

### OQ-01: none blocking

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: the design is human-resolved in DECISIONS.md D141 (two-way reconciliation; out-of-scope = recorded reason, in-scope-unmodified = one-word acknowledgment; finalize is the mandatory chokepoint; surfaces + attributes, does not judge; begin's frozen `Scope-Paths` unchanged). The en-route `scope add` verb that D141 mentioned as OPTIONAL was DROPPED at /plan-review (2026-08-24) as over-scope; the interactive+headless reconciliation at finalize fully covers the need. No blocking open question remains.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: tests show (TTY) an out-of-scope changed path prompts for and RECORDS a reason then proceeds (empty reason does NOT finalize); a declared-but-unmodified path prompts for and records a one-word acknowledgment then proceeds; both appear in ONE batched prompt; a clean delta produces NO prompt and finalizes silently; (HEADLESS) the same out-of-scope path answered via `--scope-reason <path>=<why>` records the reason and proceeds, and a declared-but-unmodified path answered via `--scope-ack <path>` proceeds; (HEADLESS, missing answers) a non-empty delta with no flags FAILS CLOSED with a result that names each unanswered path and the exact `aw ipd finalize ... --scope-reason/--scope-ack ...` command (does not hang, does not skip).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the full reconciliation test set (both directions; the batched TTY prompt; the headless `--scope-reason`/`--scope-ack` channel; the clean no-op; the headless-missing fail-closed naming the exact command; and verbatim durable attribution in the terminal history) passes; `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - the finalize two-way scope reconciliation (surface + attribute both deltas at the unskippable step), via an interactive prompt and a non-interactive flag channel.

### Execution contract

1. Open questions RESOLVED: no blocking OQ (design fixed by DECISIONS.md D141). PREREQUISITE: extends `aw ipd finalize` (Order 04) and reuses its scope-delta computation, so execute AFTER Order 04; if Order 04's delta computation is not available, STOP and report rather than recomputing it differently.
2. Scope fence: touch ONLY the single-IPD lifecycle module, `cli.py` (finalize reconciliation prompt + `--scope-reason`/`--scope-ack` flags + help), `tests/test_ipd_lifecycle_cli.py`, and the lifecycle doc/spec via managed verbs. Do NOT add an en-route `aw ipd scope add` verb (dropped at /plan-review), do NOT change `aw ipd begin`'s frozen `Scope-Paths`, do NOT build rollback (Order 06) or remove the bypass (Order 07). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via `aw ipd finalize` (append the `## Workflow history` line, set `Status: executed`, move the plan, path-scoped lifecycle commit); if the finalizer cannot finalize this plan, STOP and report.
