# IPD: Enforce single-IPD lifecycle and scope gates (fail-closed)

- Date: 2026-08-23
- Kind: orchestrator
- Concern: Verification of the executed IPD p7dqwz found that the executor delivered the requested product work but (a) committed an out-of-scope `tests/test_empty_state_ux.py` change in commit 57a70b0, outside p7dqwz's hard scope fence, and (b) left a terminal record carrying the generic `executed (aw set)` actor with no durable pre-execution / pre-transition gate evidence. Prose-only STOP rules did not contain the behavior, and `aw set executed` still provides an ungated terminal-transition bypass. This Set replaces the prose safeguards with machine-checkable, fail-closed lifecycle gates for the ordinary single-IPD path.
- Scope: Orchestrates a seven-child Set that (1) owns the concrete p7dqwz test-scope residue, (2) adds a machine-readable `Scope-Paths` allowlist to the IPD schema with a grandfather policy, (3) adds a fail-closed `aw ipd begin` execution-start receipt, (4) adds an atomic `aw ipd finalize` terminal transaction, (5) adds finalize's two-way scope reconciliation (out-of-scope changed path -> recorded reason; in-scope-unmodified path -> acknowledgment; DECISIONS.md D141), (6) adds finalize rollback/failure semantics, and (7) removes the raw terminal-transition bypasses and strengthens history-attribution lint. Touches agent_workflows/{ipd_schema.py,ipd_lint.py,ipd_authoring.py,status_set.py,cli.py,run_freeze.py} plus one narrowly-named new single-IPD lifecycle module, tests/test_empty_state_ux.py, focused tests/test_ipd_*.py + tests/test_status_set.py + a new lifecycle test file, the implemented IPD lifecycle spec (via its managed verb), .aw/system/workflows/ipd-lifecycle/, .aw/records/plans/README.md, CONTRIBUTING.md, and required CLI/help/installer parity surfaces. Does NOT implement autonomous Set execution (that is the reviewed execset Set), retrofit or edit any terminal IPD (including p7dqwz), rewrite the run ledger, or change product behavior unrelated to IPD execution fidelity.
- Status: to-review
- Set: ipdgates
- Order: 0
- Highest E allocated: 02
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: do64fh

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created as the decomposition of the REJECT-NEEDS-REPLAN single IPD 39fz2x (ipdfidelity-01), per its OQ-05 blueprint and the human's /plan-review decision to decompose into an orchestrated Set.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Verified all six child-table filenames resolve to real (truncated) on-disk files and match cited Ids/orders. PR-001/PR-002 (HIGH-value self-bootstrap gap: the orchestrator self-finalizes via `aw ipd finalize`, which requires a begin receipt + `Scope-Paths` comparison that Order 02 makes hard-required for post-cutoff plans - but NO ipdgates plan carries `Scope-Paths`, and the Set is authored before Order 02 ships, so the Set would circularly block its own gates; added a `## Self-bootstrap` section grandfathering the ipdgates Set's own plans as Scope-Paths-advisory, tying the cutoff to Order 02's OQ-01, and requiring the finalize grammar to allow a grandfathered plan to finalize via the implicit lifecycle-artifact exception; added matching completion + cross-IPD criteria); PR-003 (E-01 now enumerates the Set-wide blocking-OQ ledger: Order 02/03/04/06 OQ-01, currently OPEN pending per-child review). Verified Order 02 (Scope-Paths required post-cutoff) and Order 04 (finalize requires receipt+comparison) against their files.
- 2026-08-23 renumber+new-child (opencode its_direct/pt3-claude-opus-4.8-1m-us): inserted a new Order 05 (`qmt3yk`, finalize two-way scope reconciliation, DECISIONS.md D141) split out of Order 04 at human direction; rollback moved 05 -> 06 (`3xh53a`), remove-bypass 06 -> 07 (`wezhxg`). Updated the child table (now 01-07), the execution-order + lifecycle-move sequence (02->03->04->05->06->07), and added the reconciliation to completion criteria + cross-IPD validation. Reset to `to-review` because the child set + sequence changed materially. The unrelated `unifyfileio` Set's own Order 05 is a different Set and was not touched.
- 2026-08-23 consistency-fix (opencode its_direct/pt3-claude-opus-4.8-1m-us): post-renumber Set audit corrected residual "six-child"/"Orders 01-06" counts to seven/01-07 (Scope enumeration now includes reconciliation as item 5; E-01/E-02/V-01/V-02/cohesion counts); and fixed the E-01 blocking-OQ ledger (the attribution-lint OQ is Order 07 OQ-01 not "Order 06 OQ-01"; added Order 07 OQ-02; marked all blocking OQs resolved per the completed per-child reviews). The prior `/plan-review` history line above is left verbatim as the immutable record of that (then-six-child) review.

## Goal

Make ordinary single-IPD execution FAIL CLOSED when an executor expands the reviewed file scope or skips a lifecycle gate, replacing today's prose-only safeguards with commands and receipts an executor cannot truthfully bypass and still reach `Status: executed`. Concretely: own the one beneficial-but-unauthorized p7dqwz test change prospectively; give every post-cutoff IPD a machine-readable `Scope-Paths` allowlist; require a frozen pre-execution receipt (`aw ipd begin`) bound to the approved plan and base HEAD; make terminal transition a single atomic, evidence-emitting transaction (`aw ipd finalize`) that compares actual changed paths against the allowlist and refuses unexplained paths; make that transaction safely rollback-able; and remove the raw `aw set executed` plan-terminal bypass so no public CLI path can reach `executed` without the receipt, scope comparison, three lint gates, attributed history, and lifecycle commit.

Non-goal: this Set does not build autonomous multi-IPD Set execution (the reviewed `execset` Set owns that and will REUSE the begin/finalize primitives this Set delivers), does not retrofit terminal IPDs, and does not enforce general git policy outside IPD execution.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Orchestrate the seven-child lifecycle-gate Set

- [ ] E-01 Confirm the seven child IPDs (Orders 01-07) are authored, `aw ipd lint`-conforming, and their dependency order is recorded in the child table below; do not execute a child until (a) its `Depends on` predecessors are executed with clean manifests, AND (b) every BLOCKING open question it carries is human-resolved. The blocking-OQ ledger across this Set (all human-resolved as of 2026-08-23 during per-child `/aw plan-review`; re-verify none reverted before executing): Order 02 OQ-01 (grandfather-cutoff representation) - resolved; Order 03 OQ-01 (begin-receipt location + lifetime) - resolved; Order 04 OQ-01 (what "this execution's changes" means vs concurrent edits) - resolved; Order 07 OQ-01 (attribution-lint forward-only vs repo-wide) - resolved; Order 07 OQ-02 (which plan-terminal statuses the raw path gates) - resolved. Orders 01, 05, and 06 carry no blocking OQ. A child with any unresolved blocking OQ is NO-GO and MUST NOT be executed.
  - Depends on: none
  - Expected outcome: the Set is coherent and each child is ready for per-child human approval, blocking-OQ resolution, and sequential execution.
  - Execution state: pending

- [ ] E-02 After all seven children are executed, run the Cross-IPD validation below (one lifecycle module, three gates enforced, no raw terminal bypass remains, grandfather policy holds, self-finalize dogfood succeeded) and confirm the full suite is green; then transition this orchestrator to executed via `aw ipd finalize` (dogfooding the primitive the Set built).
  - Depends on: E-01
  - Expected outcome: the whole Set is verified and the orchestrator is closed through the very lifecycle it created.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (Id) | What it does | Depends on |
|---|---|---|---|
| 01 | `20260823-ipdgates-01-v6zie5-own-and-regression-test-the-p7dqwz-xdg-config-isolation-resi.ipd.md` | Own + regression-test the out-of-scope `tests/test_empty_state_ux.py` XDG isolation p7dqwz committed without authority. | none |
| 02 | `20260823-ipdgates-02-oorry1-canonical-scope-paths-allowlist-schema-and-grandfather-polic.ipd.md` | Add the machine-readable `Scope-Paths` allowlist to the IPD schema/scaffold/parser/lint, with the pre-cutoff grandfather/advisory policy. | none |
| 03 | `20260823-ipdgates-03-xjbvu2-aw-ipd-begin-fail-closed-execution-start-receipt.ipd.md` | `aw ipd begin`: fail-closed pre-execution receipt (pre-execution lint + `run_freeze` + base-HEAD/actor binding + atomic resumable write). | 02 |
| 04 | `20260823-ipdgates-04-v7e88a-aw-ipd-finalize-atomic-terminal-transaction.ipd.md` | `aw ipd finalize`: the single atomic terminal transaction (receipt validation, pre-transition lint, scope comparison, history, status/move, index refresh, path-scoped commit, post-transition lint, evidence). | 03 |
| 05 | `20260823-ipdgates-05-qmt3yk-finalize-two-way-scope-reconciliation-unexpected-path-reason.ipd.md` | finalize's two-way scope reconciliation (DECISIONS.md D141): out-of-scope changed path -> recorded reason; in-scope-unmodified path -> one-word acknowledgment; one batched prompt at the unskippable step; optional en-route `aw ipd scope add`; surfaces + attributes, does not judge. | 04 |
| 06 | `20260823-ipdgates-06-3xh53a-aw-ipd-finalize-rollback-and-failure-semantics.ipd.md` | finalize's two-phase failure semantics: pre-commit rollback; post-commit incomplete-reporting without history rewrite; its own adversarial tests. | 05 |
| 07 | `20260823-ipdgates-07-wezhxg-remove-raw-terminal-transition-bypasses-and-strengthen-histo.ipd.md` | Refuse/delegate raw `aw set executed` / `aw ipd set executed` plan-terminal transitions into finalize; require non-generic actor/model + nonempty summary in post-transition history lint. | 04, 05, 06 |

Execution order: 01 and 02 have no dependency and may run first in either order; then 03 -> 04 -> 05 -> 06 -> 07. Order 01 (the p7dqwz residue) is independent and could be done at any point; it is listed first because it closes the concrete observed defect. The lifecycle chain 02->03->04->05->06->07 is strict because each builds on the prior primitive (04 computes the scope delta; 05 reconciles it; 06 makes the transaction rollback-safe; 07 removes the raw bypass once finalize is complete).

## Completion criteria (the whole Set is done only when)

- The p7dqwz `tests/test_empty_state_ux.py` XDG isolation is owned by Order 01 with a failing-without-isolation regression case; no application file changed for it.
- `Scope-Paths` exists in the canonical IPD schema, scaffold, parser, and lint; a post-cutoff plan without it is refused at approval/pre-execution while pre-cutoff reviewed pending plans (the `unifyfileio` and `execset` Sets) get only an ADVISORY diagnostic (grandfathered).
- `aw ipd begin` produces a fail-closed receipt bound to plan Id + digest + base HEAD + actor/model + timestamp; nonconforming lint, dirty/ambiguous baseline, or missing actor yields NO valid receipt.
- `aw ipd finalize` is the ONLY supported single-IPD terminal transaction; it catches the exact p7dqwz failure signatures (an extra `tests/test_empty_state_ux.py` path; absent pre-execution/pre-transition evidence), reconciles the scope delta in BOTH directions (out-of-scope changed path -> recorded reason; in-scope-unmodified path -> acknowledgment; Order 05, D141), emits captured gate evidence, and is rollback-safe (Order 06).
- No public CLI path (`aw set executed`, `aw ipd set executed`, or an alias) can move an IPD to `executed` without the receipt, scope comparison, three lint gates, attributed history, and lifecycle commit; post-transition lint rejects `executed (aw set)`-style generic-actor entries.
- The `ipdgates` Set's own plans were treated as grandfathered `Scope-Paths`-advisory (per the Self-bootstrap section), so the Set could build and then pass its own gates without circular blocking.
- This orchestrator was itself finalized via `aw ipd finalize` (self-dogfood) as a grandfathered plan using the implicit lifecycle-artifact exception, and `pytest -n auto` is green with `aw check all` showing no new Set-attributable findings.

## Cross-IPD validation

- **One lifecycle module:** the begin/finalize logic lives in a single narrowly-named module reused by both commands (and callable by the future `execset` Set); a test asserts there is not a second parallel finalize path.
- **Three gates enforced end-to-end:** an integration test drives begin -> work -> finalize and asserts all three lint phases (pre-execution, pre-transition, post-transition) ran and their outputs are captured in the receipt/report.
- **Two-way scope reconciliation (Order 05, D141):** an integration test proves finalize surfaces both delta directions - an out-of-scope changed path requires a recorded reason (empty reason does not finalize), an in-scope-unmodified path requires a one-word acknowledgment - both captured verbatim in the terminal record; a clean delta is a silent no-op; a headless run with a non-empty delta and no answers fails closed.
- **No raw bypass remains:** a test enumerates the plan-terminal CLI aliases and asserts every one refuses and points to `aw ipd finalize`.
- **Grandfather holds:** a fixture standing in for a pre-cutoff reviewed sibling (unifyfileio/execset) is NOT blocked from approval by the missing `Scope-Paths`; a post-cutoff fixture IS.
- **Self-dogfood + grandfather:** the orchestrator's own terminal transition used `aw ipd finalize` (recorded in its workflow history and the finalize evidence), not a raw transition, AND it succeeded as a grandfathered `Scope-Paths`-advisory plan via the implicit lifecycle-artifact exception (proving the Set's own plans are not circularly blocked by the requirement they introduce).
- **Whole-suite regression:** `pytest -n auto` green; pasted in E-02 here and in each child's V-items.

## Self-bootstrap (this Set creates the very gates it must pass)

This Set BUILDS the `Scope-Paths` requirement (Order 02) and the `aw ipd begin`/`aw ipd finalize` commands (Orders 03/04), then requires its own later members AND this orchestrator to finalize through them (self-dogfood). That is circular unless the bootstrap order is explicit:

- **The `ipdgates` Set's own plans are GRANDFATHERED** with respect to the `Scope-Paths` hard-requirement: they were authored BEFORE Order 02 ships the requirement, so - exactly like the `unifyfileio`/`execset` siblings (OQ-01) - they are `Scope-Paths`-advisory, not blocked. A plan cannot be hard-gated by a field its own Set is still introducing. This grandfathering is governed by Order 02's OQ-01 cutoff decision (still OPEN, human-owned); whichever cutoff representation Order 02 adopts MUST classify the `ipdgates` plans as pre-cutoff/advisory.
- **Bootstrap execution order for the self-dogfood:** Orders 01, 02, 03 are transitioned with the EXISTING lifecycle workflow (the new commands do not exist yet). Order 04 is the FIRST plan that MAY finalize via the just-built `aw ipd finalize`. Orders 05, 06, and THIS orchestrator finalize via `aw ipd finalize`. For the orchestrator's own self-finalize to work while it is grandfathered (no `Scope-Paths`), Order 02's grammar MUST allow a grandfathered plan to finalize with the implicit lifecycle-artifact exception (its own plan file + index refresh) rather than requiring a declared allowlist. If `aw ipd finalize` cannot finalize a grandfathered plan, STOP and report - do not fall back to a raw transition.
- If, when Order 04/06 land, self-finalizing a grandfathered `ipdgates` plan is not yet supported by the finalize grammar, that is a real gap to fix in Order 02/04 (or a corrective), NOT a reason to hand-edit status.

## Deferred / out of scope (with reason)

- Autonomous Set scheduling, worker routing, cross-worktree integration: owned by the reviewed `execset` Set; this Set delivers only the single-IPD begin/finalize primitives execset will reuse.
- Retrofitting or editing p7dqwz or any other terminal IPD: prohibited; their historical evidence gaps stay historical. This Set prevents recurrence and owns the one beneficial out-of-scope test change (Order 01).
- General git-commit-policy enforcement outside IPD execution: out of scope.
- Semantic verification of whether code honors intent: remains `/verify-execution` work; this Set enforces declared path scope and lifecycle proof, not semantic correctness.

## Scope check

- Over-scope: none. Each child is one lifecycle-gate concern.
- Under-scope: none. The concrete residue, machine-readable scope, execution-start receipt, atomic terminal transaction, rollback semantics, and bypass removal are each an independently-executable child.

## Required tests / validation

- Each child carries its own falsifiable V-items with pasted evidence.
- This orchestrator's E-02 runs the Cross-IPD validation after all children land, dogfoods `aw ipd finalize` for its own transition, and pastes `pytest -n auto` output.

## Open questions

### OQ-01: Does the new `Scope-Paths` requirement retroactively gate the already-reviewed pending sibling Sets?

- Blocking: no
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED (human, 2026-08-23, inherited from the 39fz2x review): NO. Plans reviewed before this Set ships (the `unifyfileio` and `execset` Sets) are grandfathered `Scope-Paths`-optional and receive only an ADVISORY (non-blocking) migration diagnostic; only plans authored or re-reviewed after the grandfather cutoff are hard-required to carry `Scope-Paths`. Order 02 implements the cutoff; the orchestrator records it so the whole Set honors it.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `aw ipd lint --agent` reports `conforming` for all seven children and this orchestrator; the child table lists all seven with the recorded dependency order; each child's blocking OQs are enumerated.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: after all seven children are executed, the Cross-IPD validation tests pass; the orchestrator's own terminal transition was performed by `aw ipd finalize` (evidence pasted); `pytest -n auto` is green (pasted); `aw check all` shows no new Set-attributable findings (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one program - fail-closed single-IPD lifecycle/scope enforcement - decomposed into seven dependency-ordered children each executable and verifiable in one focused pass.

### Execution contract

1. Open questions RESOLVED: orchestrator OQ-01 (grandfather) resolved; each child carries its own open questions and must resolve any blocking one before its execution.
2. Scope fence: this orchestrator makes NO product code changes itself; all code changes happen in the children within their own scope fences. Do not expand a child's scope; if a child seems to need more, STOP and report or re-review that child.
3. Honesty rule (hard MUST): when reporting tests/gates passed, paste the ACTUAL runner output and durable receipt path/digest; never claim a pass from narration or an unchecked box.
4. Commit ONLY this Set's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push. Leave the concurrent `unifyfileio`/`execset` edits and their index state untouched.
5. Lifecycle move: execute children in order (01/02 first, then 03->04->05->06->07), each transitioning to executed on its own completion. Bootstrap: Orders 02/03/04 build the begin/finalize commands, so early children use the existing lifecycle workflow; once `aw ipd finalize` is complete (forward transaction 04 + reconciliation 05 + rollback 06) and the raw bypass is removed (Order 07), later children AND this orchestrator MUST finalize via `aw ipd finalize`. This orchestrator's own terminal transition is a self-dogfood of `aw ipd finalize`; if the finalizer cannot finalize it, STOP and report (never fall back to a raw transition or hand-edit status). Then append the `## Workflow history` line, set `Status: executed`, and make the path-scoped lifecycle commit as part of the finalize transaction.
