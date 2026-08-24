# IPD: Remove raw terminal-transition bypasses and strengthen history lint

- Date: 2026-08-23
- Kind: child
- Concern: Even after `aw ipd finalize` exists (Orders 04-06: forward transaction, scope reconciliation, rollback), the raw `aw set executed` / `aw ipd set executed` plan-terminal path still works - it moves the plan and writes a generic `executed (aw set)` actor with no receipt, no scope comparison, and no captured gate evidence. That is the exact bypass that produced the p7dqwz false-fidelity record. Until it is removed and the history lint rejects generic-actor terminal entries, the gates are optional.
- Scope: Make raw plan-to-terminal transitions refuse and point to `aw ipd finalize`, and strengthen post-transition history lint. Touch: agent_workflows/status_set.py (refuse plan `executed`/terminal transitions, preserve nonterminal plan transitions and non-plan artifact terminal transitions), agent_workflows/cli.py (the `set`/`ipd set` routing + help), agent_workflows/ipd_lint.py (post-transition: require a non-generic actor/model + nonempty summary), and tests/test_status_set.py + tests/test_ipd_lint.py + tests/test_ipd_lifecycle_cli.py. Does NOT build begin/finalize (Orders 03/04) - it depends on them existing.
- Status: to-review
- Set: ipdgates
- Order: 7
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: wezhxg

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-05).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (discriminate on record_type not the `executed` token - prompts share it), PR-002/OQ-02 (human: gate only executed/done, preserve superseded/not-executed retirement), PR-003 (grandfather cutoff is a hard dependency on Order 02's open OQ-01), PR-004 (pin the generic-actor predicate to the literal `aw set`, not bare tool/human names - keeps blast radius ~5 not 50+), PR-005 (hard lockout gate: do not execute until Orders 04/05 executed + finalize proven), PR-006 (validate the NEWEST terminal entry). OQ-01 human-resolved forward-only; OQ-03 human-resolved = DELEGATE `aw set executed` into finalize (not refuse-and-redirect). Added honest-limits (finalize catches out-of-scope + attribution, NOT completeness/test-sufficiency) and a Recovery-paths section (missing-receipt -> honest advisory acknowledgment NOT a back-dated begin; legitimate out-of-scope -> light-touch acknowledge-and-proceed; grandfathered -> advisory, no lockout) per human direction, plus the mid-stream-scope design tension for Orders 02/03. Verified: aw ipd finalize/begin absent, `aw set executed` ungated for plans + generic `aw set` actor (status_set.py:356,463), prompts share the executed token (status_set.py:47-59), 4 existing `(aw set)` executed records.
- 2026-08-23 renumber (opencode its_direct/pt3-claude-opus-4.8-1m-us): Order 06 -> 07 to make room for a new Order 05 (finalize two-way scope reconciliation, per DECISIONS.md D141); the prior Order 05 rollback became 06. Filename + front-matter Order updated via `aw rename`; internal "Orders 04/05" / "Order 06 itself" number references corrected to "Orders 04-06" / "Order 07"; reset to `to-review` since its lockout gate and dependency set now span the finalize orders 04-06.

## Goal

Close the raw terminal-transition bypass so no public CLI path can move an IPD to `executed` without the begin receipt, scope comparison, three lint gates, attributed history, and lifecycle commit. Make `aw set executed <plan>`, `aw ipd set executed <plan>`, and the `done` alias transparently DELEGATE into the gated `aw ipd finalize` transaction (same safety, no memorization burden - OQ-03), while PRESERVING nonterminal plan transitions (draft/to-review/reviewed/approved), plan RETIREMENT (`superseded`/`not-executed`, which finalize does not perform - OQ-02), and all non-plan artifact status changes (specs/backlog/prompts/releases). Strengthen post-transition lint so a newly-executed plan's terminal history entry MUST identify a non-generic actor/model (rejecting the machine-default `aw set`) and a nonempty summary, forward-only (OQ-01). Finalize is a double-check gate, not a correctness oracle, and every stuck case has an honest non-fabricating recovery (see the honest-limits and Recovery paths sections).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Refuse the raw plan-terminal transition

- [ ] E-01 In `status_set.py` (and the `cli.py` `set`/`ipd set` routing), make a request to move a PLAN to `executed` (or its `done` alias) TRANSPARENTLY DELEGATE into the gated `aw ipd finalize` transaction rather than performing the old ungated move; PRESERVE nonterminal plan transitions (draft/to-review/reviewed/approved), PRESERVE plan RETIREMENT transitions (`superseded`/`not-executed`, which are NOT execution and which finalize does not perform - see OQ-02), and PRESERVE all non-plan artifact terminal transitions (specs/backlog/prompts/releases). No expert escape hatch that can FAKE a successful execution (39fz2x OQ-02: none); but "no bypass" means "never fake success", NOT "no way forward" - see the Recovery paths section for the honest, non-fabricating recovery when a gate input is missing.
  - Depends on: none
  - Note (verified - DELEGATE not refuse; discriminate on record_type, NOT the status token): (1) DELEGATION (OQ-03 human decision): `aw set executed <plan>` / `aw ipd set executed <plan>` route transparently through the gated finalize path (same safety - `executed` is unreachable ungated - without forcing the human/agent to memorize a second command; self-documenting principle). It fails with a clear "what is missing / what to do" message (pointing at the Recovery paths) only when a required gate input is genuinely absent; it does NOT dead-end. (2) The delegation MUST key on `rec.record_type == "plans"` AND normalized target `executed`, inserted in `validate_transition_allowed`/`apply_status_change` (`status_set.py:317-343`) alongside the existing `specs`/`backlog` branches - NOT on the status string alone, because PROMPTS share the EXACT `executed` token and the `done->executed` alias (`status_set.py:47-59,295-297`); a token-based rule would wrongly divert prompt terminal transitions. `detect_artifact_type` reliably returns `"plans"` for `.ipd.md` (`status_set.py:139-178`).
  - Expected outcome: `aw set executed <plan>` transparently performs the gated finalize transaction; prompt/spec/backlog/release terminal transitions, plan retirement (`superseded`/`not-executed`), and nonterminal plan transitions are all unchanged.
  - Execution state: pending

### Task group 2: Strengthen attribution lint

- [ ] E-02 Strengthen post-transition lint in `ipd_lint.py`: the `executed` plan's NEWEST terminal `## Workflow history` entry (the one this transition wrote) MUST have a non-generic actor AND a nonempty summary. A generic/empty actor or empty summary is a post-transition conformance error. (Grandfather already-executed terminal records so this does not retroactively fail the existing executed tree; apply the stricter rule only to transitions performed after this ships, per OQ-01.)
  - Depends on: none
  - Note (verified - net-new parsing + two pinned predicates + hard dependency): (1) the current post-transition check (`ipd_lint.py:712-728`) only confirms SOME history line's status is `executed`; the parser `_HISTORY_LINE_RE` (`ipd_lint.py:168`) captures ONLY the status token, not the `(actor)` or `: message` - so actor/summary parsing is NET-NEW and must extend that regex/`doc.history_lines`. (2) GENERIC-ACTOR PREDICATE (pin it, do not leave "placeholder" undefined): reject the literal `aw set` (and `aw set, --by-human`), an empty actor, and a whitespace/placeholder-only actor; ACCEPT any real agent/model or human identifier. Do NOT expand "generic" to bare tool/human names like `Antigravity`/`maintainer` (that would balloon the retroactive set from ~5 lines to 50+); the target is specifically the `aw set` machine default. (3) GRANDFATHER CUTOFF is a HARD dependency on Order 02: the concrete pre/post-cutoff predicate is defined by Order 02 (its OQ-01, still open); E-02 MUST consume that predicate and MUST NOT invent its own cutoff. If Order 02's cutoff mechanism is not yet available at execution time, STOP and report rather than guessing a cutoff.
  - Expected outcome: post-transition lint rejects a generic (`aw set`)/empty actor and empty summary on the newest terminal entry going forward, keyed on Order 02's cutoff, without failing the grandfathered executed tree.
  - Execution state: pending

### Task group 3: Prove no bypass and compatibility

- [ ] E-03 Add tests: (`tests/test_status_set.py` / `tests/test_ipd_lifecycle_cli.py`) `aw set executed <plan>`/`aw ipd set executed <plan>` DELEGATE into the finalize transaction (not the old ungated move); a PROMPT terminal `executed` transition, spec `implemented`, backlog `done`, release `shipped`, plan retirement `superseded`/`not-executed`, and nonterminal plan transitions all retain their existing behavior (proving the discriminator is record_type+executed, not the status token); the Recovery paths behave honestly (missing-receipt -> advisory acknowledgment, NOT a fabricated back-dated begin; a legitimate out-of-scope edit -> light-touch acknowledge-and-proceed; grandfathered/no-Scope-Paths -> advisory, no lockout); (`tests/test_ipd_lint.py`) post-transition lint rejects the literal `aw set`/empty actor + empty summary on the newest terminal entry and accepts a real agent/model + summary, and does NOT fail a grandfathered pre-cutoff executed record; and CLI help/workflow docs advertise no ungated bypass. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: no public CLI path reaches plan `executed` ungated; delegation + compatibility (prompts/specs/backlog/releases/retirement/nonterminal) proven; attribution lint enforced forward without retroactive breakage; every stuck case has a proven honest recovery (no lockout, no fabrication).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `status_set.py` currently accepts plan `executed`, writes/moves the file, auto-refreshes indexes, and swallows index exceptions (`status_set.py:580,617`); it is the exact bypass. The p7dqwz executed record carries `- 2026-08-23 executed (aw set): status set to executed`.
- `aw set` is untyped (transitions plans/specs/prompts/backlog); only the PLAN terminal transition is being removed - the others stay.
- 39fz2x OQ-02 (human-inherited): no raw terminal escape hatch.
- Depends on `aw ipd finalize` (Orders 04-06: forward transaction, scope reconciliation, rollback) existing, since the delegated/only-supported path routes into it.

## Findings

Removing the bypass is what makes the gates mandatory rather than optional. It must be surgical: only the plan-to-terminal transition is removed; nonterminal plan transitions and all non-plan artifact transitions are load-bearing and must be preserved. The attribution lint prevents a future generic-actor terminal entry from recurring, but must grandfather the existing executed tree to avoid mass retroactive failure.

## What finalize can and cannot enforce (honest limits)

Removing the bypass is a DOUBLE-CHECK gate ("did you do what you said, and only that?"), NOT a correctness oracle. State this so nobody over-trusts it:

- CAN enforce deterministically: (i) an execution that edited a path OUTSIDE the frozen `Scope-Paths` (finalize diffs the begin receipt's base HEAD..now and flags any changed path not in the allowlist - this is the p7dqwz signature), and (ii) a terminal record with a greenwashed/unattributed actor or empty summary (attribution lint).
- CANNOT enforce: whether the agent SKIPPED files it should have changed (no machine oracle for "intended but forgot"), or whether the tests were SUFFICIENT (only that pasted output exists, not that it is deep). Those remain the job of the V-item evidence, a fresh-context verifier, and human review. Do not claim finalize guarantees completeness or test quality.

## Recovery paths (no bypass MUST NOT mean no way forward)

"No escape hatch" (39fz2x OQ-02) means finalize never FAKES a successful execution; it does NOT mean an IPD can get stuck erroring forever. Each stuck case has an honest, non-fabricating recovery that CAPTURES THE TRUTH of the misstep and lets the agent/human move on - never re-enacting a step that did not happen:

1. MISSING begin receipt (executed without ever running `aw ipd begin` - the common pre-cutoff/grandfathered case, or a forgotten `begin`): DO NOT retroactively run `begin` (back-dating a start that never happened is a lie). Instead finalize records an HONEST terminal-history acknowledgment (e.g. "executed without a pre-execution receipt; scope checked retroactively against current state on <date>, NO frozen baseline") and proceeds, running whatever checks it can, LABELED "retroactive/advisory" - never labeled "verified against a receipt". The misstep is captured, not erased.
2. REAL out-of-scope edit that is legitimate (mid-stream you had to touch a file the plan did not foresee - which in complex work is often the RULE, not the exception): LIGHT TOUCH. The gate exists to make you NOTICE and CONFIRM, not to force a rewrite. Acknowledge/own it - widen `Scope-Paths` with a note (re-review if the plan is approved), or record an accepted deviation in the terminal history - and move on. Only REVERT if the change is genuinely wrong. A clean in-scope diff passes silently.
3. GRANDFATHERED / no `Scope-Paths` declared (this Set's own plans and all pre-existing pending plans predate the machinery): the scope check is ADVISORY-ONLY, recorded as such; finalize proceeds. No lockout of the grandfathered tree (including this Order 07 itself).

Design tension to carry into Orders 02 (`Scope-Paths` schema) and 03 (`begin`): because unforeseen-but-legitimate mid-stream edits are common in complex work, the `Scope-Paths` allowlist and the begin/finalize ergonomics MUST make owning such an edit LIGHT-TOUCH (acknowledge + proceed), not a straitjacket that punishes normal development. The gate's purpose is a double-check, not a barrier to mid-stream discovery.

## Proposed changes (ordered, validatable)

1. Delegate `aw set executed <plan>`/`done` into the gated `aw ipd finalize` transaction (keyed on record_type==plans), preserving retirement + all non-plan transitions; provide the honest, non-fabricating Recovery paths for missing-receipt / legitimate-out-of-scope / grandfathered cases (E-01).
2. Strengthen post-transition attribution lint (reject the literal `aw set`/empty actor + empty summary on the newest terminal entry), forward-only, grandfathering existing executed records (E-02).
3. Prove delegation + no-ungated-bypass + compatibility (prompts/specs/backlog/releases + retirement preserved) + attribution-lint-forward-only + the recovery paths (E-03).

## Deferred / out of scope (with reason)

- Building begin/finalize: Orders 03/04 (dependencies).
- General git policy outside IPD terminal transitions: out of scope.

## Scope check

- Over-scope: none.
- Under-scope: none; bypass removal, attribution lint, and compatibility/no-bypass tests are included.

## Required tests / validation

- `tests/test_status_set.py`, `tests/test_ipd_lint.py`, `tests/test_ipd_lifecycle_cli.py` per E-03.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Update the IPD lifecycle spec + workflow doc + `.aw/records/plans/README.md` + `CONTRIBUTING.md` + CLI help (via managed verbs) so the plan-`executed` terminal transition is documented as going through `aw ipd finalize` (whether invoked directly or via the delegating `aw set executed`), no ungated bypass is advertised, and the Recovery paths (missing-receipt acknowledgment, light-touch scope-deviation ownership, grandfathered advisory) are documented so a stuck IPD has a clear honest way forward. Document that plan RETIREMENT (`superseded`/`not-executed`) remains the separate RETIRED-header + `git mv` flow, unchanged.

## Open questions

### OQ-01: Is the attribution-lint stricter rule forward-only (grandfather the existing executed tree) or repo-wide?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): FORWARD-ONLY (option A). Apply the stricter actor/summary rule only to transitions after this ships, keyed on Order 02's cutoff; grandfather the existing executed tree. Rationale: repo-wide would retroactively fail the existing ~270-file executed tree (at least the 4 `(aw set)` files, potentially more) and would require editing IMMUTABLE terminal records, violating the immutable-terminal-record convention. Consistent with orchestrator 00's resolved forward-only policy.

### OQ-02: Which plan-terminal statuses does E-01 refuse - only `executed`/`done`, or also `superseded`/`not-executed`?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): gate ONLY `executed` (and its `done` alias) - the execution terminal that `aw ipd finalize` owns. PRESERVE the raw path for `superseded` and `not-executed`, because those are RETIREMENT (not execution): the documented flow is a `RETIRED ...` header + `git mv` to `superseded/`/`not-executed/` (AGENTS.md), which `aw ipd finalize` does NOT perform - redirecting them to `finalize` would be wrong. `reusable` is a standing disposition, not terminal, and is unaffected. E-01 gates only `record_type == "plans"` AND normalized target in {`executed`}.

### OQ-03: Does `aw set executed <plan>` REFUSE-and-redirect, or transparently DELEGATE into finalize?

- Blocking: no
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): DELEGATE. `aw set executed <plan>` transparently performs the gated `aw ipd finalize` transaction rather than refusing and telling the human to retype a different command. Same safety (executed is unreachable ungated) with no memorization burden (self-documenting principle). It surfaces a clear "what is missing / what to do next" message (per Recovery paths) only when a gate input is genuinely absent; it never dead-ends with a bare refusal.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: tests show `aw set executed <plan>` and `aw ipd set executed <plan>` refuse with a single `aw ipd finalize` next action; CRUCIALLY a PROMPT terminal transition to `executed` still SUCCEEDS (proving the refusal keys on `record_type == "plans"`, not the shared `executed` token); nonterminal plan transitions (draft/to-review/reviewed/approved) and non-plan artifact terminal transitions (spec `implemented`, backlog `done`, release `shipped`) still succeed unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: post-transition lint rejects the literal generic (`aw set`) actor, an empty actor, and an empty summary on the NEWEST terminal entry, and accepts a real agent/model + nonempty summary; it does NOT reject bare tool/human names (e.g. `Antigravity`, `maintainer`) - only the `aw set` machine default; per OQ-01 + Order 02's cutoff it does NOT fail a grandfathered pre-cutoff executed record (verify against a real pre-cutoff record such as one of the existing `(aw set)` executed files).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the delegation, no-ungated-bypass, compatibility (prompt/spec/backlog/release/retirement/nonterminal preserved), attribution, and the three Recovery-path tests (missing-receipt advisory acknowledgment with NO fabricated begin; legitimate out-of-scope light-touch acknowledge-and-proceed; grandfathered advisory no-lockout) all pass; CLI help/workflow docs advertise no ungated bypass and document the recovery paths; `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - remove the raw plan-terminal bypass and enforce attributed terminal history, surgically preserving all other transitions.

### Execution contract

1. Open questions RESOLVED (all human-resolved 2026-08-23, /plan-review): OQ-01 forward-only attribution lint; OQ-02 gate only `executed`/`done` (retirement `superseded`/`not-executed` preserved); OQ-03 DELEGATE `aw set executed` into finalize (not refuse-and-redirect). The Recovery paths + honest-limits are specified above.
1a. LOCKOUT GATE (hard MUST): this plan removes the ONLY working plan-terminal path, so it MUST NOT execute until Orders 04, 05 AND 06 are EXECUTED and `aw ipd finalize` (forward transaction + scope reconciliation + rollback) is proven to work end-to-end (there is NO escape hatch by design - 39fz2x OQ-02). Executing this order before finalize exists/works is an UNRECOVERABLE lockout (no way to finalize any plan). Confirm finalize works on a real plan before removing the bypass; if it does not, STOP and report.
2. Scope fence: touch ONLY `status_set.py`, `cli.py` (set/ipd set routing + help), `ipd_lint.py` (post-transition attribution), the three named test files, and the lifecycle doc/spec/README/CONTRIBUTING via managed verbs. Do NOT build begin/finalize. Preserve nonterminal plan transitions and non-plan artifact terminal transitions. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via `aw ipd finalize` - append the `## Workflow history` line, set `Status: executed`, move the plan, path-scoped lifecycle commit - and if the finalizer cannot finalize this plan, STOP and report (never fall back to the raw transition this very plan just removed).
