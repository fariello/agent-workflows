# IPD: Corrective: enforce single-IPD lifecycle and scope gates

- Date: 2026-08-23
- Kind: child
- Concern: Verification of executed IPD p7dqwz found that Gemini completed the requested product work but committed an unrelated test change outside a hard scope fence and left no durable proof of the mandatory pre-execution and pre-transition gates. Prose-only STOP rules are not containing repeated executor behavior, while `aw set executed` still provides an ungated terminal-transition bypass.
- Scope: Correct the specific p7dqwz test-scope residue; add a machine-readable IPD path allowlist and frozen execution-start receipt; add guarded single-IPD begin/finalize commands; block raw plan-to-terminal status transitions; strengthen lifecycle history validation, docs, and focused tests. Reuse run_freeze and existing path-scope verification primitives. Do not implement autonomous Set execution, rewrite the run ledger, retrofit terminal IPDs, or alter product behavior unrelated to IPD execution fidelity.
- Status: reviewed
- Set: ipdfidelity
- Order: 1
- Highest E allocated: 05
- Author: OpenAI Codex
- Id: 39fz2x

## Workflow history

- 2026-08-23 to-review (OpenAI Codex): created from independent verify-execution findings for p7dqwz; substantive delivery succeeded, but deterministic scope and lifecycle enforcement were bypassable.
- 2026-08-23 draft (OpenAI Codex): created.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REJECT - NEEDS REPLAN (decompose). Approach is SOUND and factually verified (57a70b0 did edit tests/test_empty_state_ux.py outside p7dqwz's fence; p7dqwz record carries 'executed (aw set)'; run_freeze.freeze_requirements at run_freeze.py:131 and status_set index-swallow at status_set.py:580,617 confirmed), but PR-001 (HIGH): E-02/E-03/E-04 are conceptually over-dense (E-04 alone bundles ~6 deliverables incl. two-phase rollback); human chose to DECOMPOSE into an orchestrated Set - re-authoring one IPD into a 00+children Set is not a bounded in-place revision, hence REPLAN with the blueprint recorded under OQ-05. Fixed in place: PR-002/OQ-03 (grandfather pre-cutoff reviewed siblings as Scope-Paths-advisory, human-confirmed; E-02/V-02 updated), PR-003/OQ-04 (self-finalize/bootstrap order added to gate item 5), PR-004 (added ### Execution contract subheading). This plan is retained in pending/ as the decomposition source; do NOT execute it as a single IPD.

## Goal

Make ordinary single-IPD execution fail closed when an executor expands the reviewed file scope or skips lifecycle gates. Close the concrete p7dqwz residue without editing its executed IPD, then replace the current prose-only safeguards with commands and receipts that Gemini or any other executor cannot truthfully bypass and still reach `Status: executed`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Close the concrete p7dqwz residue

- [ ] E-01 Adopt the out-of-scope `XDG_CONFIG_HOME` isolation from commit 57a70b0 as an explicit corrective change: extract or name the isolation mechanism clearly in `tests/test_empty_state_ux.py`, add a regression case proving a hostile external Agent Workflows config cannot influence `ReadListVerbsEmptyStateSurfaceTests`, and cite p7dqwz plus 57a70b0 in the test rationale. Do not alter application behavior.
  - Depends on: none
  - Expected outcome: the previously unauthorized test edit is independently owned by this corrective IPD and its necessity is demonstrated by a failing-without-isolation regression case.
  - Execution state: pending

### Task group 2: Machine-readable execution scope

- [ ] E-02 Extend the canonical IPD schema, scaffold, parser, and lint checkpoints with a reviewed `Scope-Paths` allowlist of repo-relative literal paths or bounded pathspecs. Define safe grammar, implicit lifecycle-artifact exceptions, generated-file treatment, and actionable diagnostics. Require the allowlist before approval/pre-execution for new or re-reviewed plans; do not silently infer it from free-form `Scope:` prose or claim legacy terminal plans conform. NON-RETROACTIVITY (OQ-03, resolved): the requirement MUST NOT retroactively block the already-reviewed pending sibling Sets that predate this plan (`unifyfileio` g6mbht/o6b8l3/laykok/3cmnfc/52zgqr; `execset` 5ahblp/iy1a2g/3m4e54/m2wwns/31744f/2h7777). Those are grandfathered as `Scope-Paths`-optional: a nonterminal plan lacking `Scope-Paths` emits an ADVISORY migration diagnostic (never an approval-blocking error) unless/until it is re-reviewed after this plan lands. Only plans authored or re-reviewed AFTER this plan ships are hard-required to carry `Scope-Paths`. Record the grandfather cutoff explicitly so the diagnostic can tell "pre-cutoff, advisory" from "post-cutoff, required".
  - Depends on: none
  - Expected outcome: an approved (post-cutoff) IPD exposes one deterministic allowlist that tooling can compare with real changed paths; existing terminal records and pre-cutoff reviewed pending plans remain non-blocked, receiving only an advisory migration diagnostic.
  - Execution state: pending

### Task group 3: Gate receipt at execution start

- [ ] E-03 Add `aw ipd begin <plan> --actor <agent/model>` as the authoritative single-IPD execution entry. It must run `aw ipd lint --phase pre-execution`, freeze the plan requirements and `Scope-Paths` with existing `run_freeze` primitives, bind the receipt to plan Id, plan digest, base HEAD, actor/model, and timestamp, and atomically write a resumable local lifecycle receipt. Exit 1 or 2, dirty/ambiguous baseline state, missing actor/model, or nonconforming lint must produce no valid receipt and no execution authority.
  - Depends on: E-02
  - Expected outcome: execution cannot later finalize without independently inspectable proof that the approved plan and scope passed the pre-execution gate at a specific base HEAD.
  - Execution state: pending

### Task group 4: Atomic terminal finalization

- [ ] E-04 Add `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` as the only supported single-IPD terminal transaction. It must validate the matching begin receipt, run pre-transition lint, compare commits and current changes since the frozen base against `Scope-Paths`, fail on any unexplained path, append the required agent/model history entry, set terminal status, move the plan, refresh only owned plan-index state, create a path-scoped lifecycle commit, run post-transition lint, and report the commit plus captured gate outputs. Before its lifecycle commit, every failure must roll back the partial transition; after commit, a post-transition failure must be reported incomplete without rewriting history.
  - Depends on: E-03
  - Expected outcome: one command performs the complete lifecycle transaction and refuses the exact p7dqwz failure signatures: an extra `tests/test_empty_state_ux.py` path and absent pre-execution/pre-transition evidence.
  - Execution state: pending

### Task group 5: Remove bypasses

- [ ] E-05 Make `aw set executed`, `aw ipd set executed`, and equivalent plan terminal aliases refuse direct plan transitions and point to `aw ipd finalize`; preserve nonterminal plan transitions and non-plan artifact status changes. Strengthen post-transition lint so an executed history entry must identify a non-generic actor/model and nonempty summary rather than accepting `executed (aw set): ...`.
  - Depends on: E-04
  - Expected outcome: no public CLI path can move an IPD to `executed` without the begin receipt, scope comparison, three lint gates, attributed history, and lifecycle commit.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Executed IPDs are immutable. This plan cross-references p7dqwz and its commits but does not amend that terminal record.
- `aw ipd lint` already owns structural checkpoints, while `status_set.py` currently moves plans directly to `executed` and inserts the generic actor `aw set`. Enforcement belongs in a typed lifecycle path, not another prose warning.
- `run_freeze.freeze_requirements()` already supplies stable requirement digests; run packets and verifier-role code already carry `allowed_paths`/`forbidden_paths`. Reuse these primitives rather than creating a second digest or path-matching engine.
- The pending `execset` Set will coordinate multi-IPD execution. This corrective covers the still-unprotected ordinary single-IPD path and must expose reusable begin/finalize primitives that `execset` can call later.
- The current worktree contains unrelated edits to `unifyfileio` plans. Every implementation and lifecycle commit must remain path-scoped and must not absorb their files or generated index state attributable only to them.

## Findings

- p7dqwz E-01 through E-03 were functionally complete and independently revalidated: 8 targeted tests passed; the full suite reported 2105 passed, 1 skipped; research index check and post-transition lint were clean.
- Commit 57a70b0 also changed `tests/test_empty_state_ux.py`, outside p7dqwz's explicit `touch ONLY` fence. The change is useful test isolation, but usefulness does not authorize silent scope expansion.
- The p7dqwz durable record contains `executed (aw set)` and only claims post-transition lint. It does not retain the required pre-execution or pre-transition gate output.
- `status_set.py` currently accepts plan `executed`, writes/moves the file, auto-refreshes indexes, and swallows index-refresh exceptions. Therefore the prose lifecycle workflow can be bypassed by the most obvious CLI command.
- A scope check performed only against the final working tree is insufficient: product changes may already be committed and concurrent unrelated edits may exist. The allowlist and base must be frozen before execution, and finalization must bind evidence to that receipt.

## Proposed changes (ordered, validatable)

1. Own and regression-test the XDG test isolation that p7dqwz committed without authority.
2. Add a canonical machine-readable `Scope-Paths` contract and migration diagnostics.
3. Add a fail-closed `aw ipd begin` receipt bound to the approved plan and base HEAD.
4. Add atomic, evidence-emitting `aw ipd finalize` and reject every raw plan-terminal transition.
5. Test the exact observed failure, rollback, concurrency, generated-index, and compatibility cases.

## Deferred / out of scope (with reason)

- Autonomous Set scheduling, worker routing, and cross-worktree integration remain in the reviewed `execset` Set. This plan provides only the single-IPD lifecycle primitive that Set execution may reuse.
- Retrofitting or editing p7dqwz and other terminal IPDs is prohibited. Their historical evidence gaps remain historical; this plan prevents recurrence and owns the one beneficial out-of-scope test change prospectively.
- General git commit policy enforcement outside IPD execution is out of scope.
- Semantic verification of whether code honors intent remains `/verify-execution` work. This plan deterministically enforces declared path scope and lifecycle proof, not semantic correctness.

## Scope check

- Over-scope: none.
- Under-scope: none. The concrete residue, machine-readable scope, execution-start evidence, terminal transaction, bypass removal, docs, and adversarial tests are all included.

## Required tests / validation

- Focused tests for IPD schema/authoring/lint, status transitions, begin receipts, scope comparison, finalization rollback, index refresh, and CLI help.
- Exact counterexample fixture based on p7dqwz: allow the planned files but include `tests/test_empty_state_ux.py`; finalization must refuse with the unexpected path and leave the approved plan unmoved.
- Positive fixture with the same extra path included in reviewed `Scope-Paths`; begin, pre-transition, path comparison, lifecycle commit, and post-transition must succeed with agent/model attribution.
- Concurrency fixture proving pre-existing dirty files and unrelated concurrent work are never committed; ambiguous intervening commits fail closed with an actionable diagnostic.
- Compatibility tests proving nonterminal `aw set` transitions and non-plan artifact terminal transitions still work, while every plan-to-terminal alias refuses.
- `pytest tests/test_empty_state_ux.py tests/test_ipd_schema.py tests/test_ipd_authoring.py tests/test_ipd_lint.py tests/test_status_set.py tests/test_ipd_lifecycle_cli.py` and full `pytest -n auto`, with actual output captured.
- `aw ipd lint --phase review-finalize <this plan>`, repository index checks, and `aw sanitize --agent` before completion.

## Spec / documentation sync

- Amend the implemented IPD structure/lifecycle spec with the `Scope-Paths`, begin-receipt, and finalize transaction contract through `aw specs note`/the repository's spec workflow rather than an undocumented code-only change.
- Update `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md`, `.aw/records/plans/README.md`, `CONTRIBUTING.md`, CLI help/examples, scaffold output, and generated/installed workflow surfaces owned by the repository.
- Update the `execset` plans only through a separate reviewed amendment if their integration contract needs to name these new primitives; do not edit them opportunistically during execution.

## Open questions

### OQ-01: Should the unauthorized XDG isolation be reverted or retained?

- Blocking: no
- Status: resolved
- Owner: corrective author
- Resolution or deferral rationale: retain it because host-global Agent Workflows configuration can contaminate an isolation test, but make the reason and regression evidence explicit under E-01 so the change is no longer unowned.

### OQ-02: Should raw `aw set executed` remain as an expert escape hatch?

- Blocking: no
- Status: resolved
- Owner: corrective author
- Resolution or deferral rationale: no. An escape hatch recreates the observed bypass. Recovery from a broken finalizer must stop and report or use a separately documented repair path that cannot claim a successful execution.

### OQ-03: Does the new `Scope-Paths` requirement retroactively gate the already-reviewed pending sibling Sets (unifyfileio, execset)?

- Blocking: no
- Status: resolved
- Owner: human (confirmed at /plan-review 2026-08-23)
- Resolution or deferral rationale: NO. Plans reviewed before this plan ships are grandfathered `Scope-Paths`-optional and receive only an ADVISORY (non-blocking) migration diagnostic; only plans authored or re-reviewed after the grandfather cutoff are hard-required to carry `Scope-Paths` (E-02). This prevents a schema addition from retroactively blocking approval of ~11 already-reviewed sibling plans.

### OQ-04: How does this plan finalize ITSELF once E-05 removes the raw terminal path?

- Blocking: no
- Status: resolved
- Owner: corrective author
- Resolution or deferral rationale: this plan's own terminal transition is the FIRST real dogfood of the new `aw ipd finalize` (built in E-04), run after all E/V complete; if the just-built finalizer cannot finalize this plan, STOP and report (fix under a new corrective) - never fall back to the removed raw path or hand-edit status (gate item 5).

### OQ-05: Should the five dense E-items be decomposed into an orchestrated Set?

- Blocking: yes
- Status: resolved
- Owner: human (confirmed at /plan-review 2026-08-23; reviewer finding PR-001)
- Resolution or deferral rationale: YES - DECOMPOSE into an orchestrated Set. The count-based size lint passes (5 E-items), but E-02/E-03/E-04 each bundle multiple independent deliverables and test surfaces (E-04 alone = receipt validation + pre-transition lint + commit/worktree scope comparison + history append + status set + file move + index refresh + path-scoped commit + post-transition lint + two-phase rollback). Because re-authoring one IPD into a 00 orchestrator + children is NOT a bounded in-place revision, this plan is REJECTED - NEEDS REPLAN at review: it must be re-authored (by the author or maintainer) as the Set blueprint below, then each child re-reviewed. This plan file is retained as the source of the decomposition, not executed as-is.

## Recommended decomposition (REPLAN blueprint)

Re-author `ipdfidelity` as an orchestrated Set (00 orchestrator + children), dependency-ordered. Suggested shape (the author may refine, but each child MUST be one focused, independently-verifiable pass):

- 00 orchestrator: the single-IPD lifecycle/scope-gate program; child sequence, dependencies, whole-Set completion criteria, cross-IPD validation.
- 01 `Scope-Paths` schema authority: extend IPD schema + scaffold + parser + lint checkpoints with the `Scope-Paths` allowlist grammar, the pre-cutoff grandfather/advisory policy (OQ-03), and migration diagnostics. (Was E-02.)
- 02 `aw ipd begin` receipt: the fail-closed execution-start command, `run_freeze` integration, receipt binding (plan Id/digest/base HEAD/actor/timestamp), atomic write, resume. Depends on 01. (Was E-03.)
- 03 `aw ipd finalize` transaction: receipt validation + pre-transition lint + scope comparison + history + status/move + index refresh + path-scoped commit + post-transition lint + evidence reporting. Depends on 02. (Was E-04, core.)
- 04 finalize rollback + failure semantics: two-phase rollback (pre-commit rollback; post-commit incomplete-reporting without history rewrite) as its own child with its own adversarial test surface. Depends on 03. (Split from E-04.)
- 05 remove bypasses + strengthen history lint: refuse raw `aw set executed` plan-terminal transitions, point to finalize, require non-generic actor/model + nonempty summary. Depends on 03/04. (Was E-05.)
- 06 close the p7dqwz XDG test residue: own + regression-test the `tests/test_empty_state_ux.py` isolation (was E-01; independent, could even be Order 01 since it has no dependency).

The Set's own dogfood/self-finalize order (OQ-04) and the grandfather cutoff (OQ-03) carry into the orchestrator's execution contract.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a targeted regression test demonstrates that an external XDG config changes behavior without the isolation boundary and cannot influence the isolated test fixture with the corrective in place; test comments/docstring cite p7dqwz and 57a70b0; no application file changes are present in E-01's commit.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: schema, scaffold, parser, and lint tests cover valid literals/bounded pathspecs, rejected absolute/parent/repo-wide patterns, generated and lifecycle exceptions, missing-allowlist refusal at approval/pre-execution for POST-cutoff plans, ADVISORY-only (non-blocking) migration diagnostics for PRE-cutoff reviewed pending plans (asserted with a fixture standing in for a unifyfileio/execset sibling), and unchanged grandfathered-terminal behavior; canonical spec/template/docs parity checks pass.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: begin-command tests capture plan Id, requirement digest, exact Scope-Paths, base HEAD, actor/model, timestamp, and pre-execution lint output in an atomic receipt; changed requirements invalidate it; lint exit 1/2, missing actor, dirty or ambiguous baseline, and interrupted write leave no valid receipt; resume reads the same receipt deterministically.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the p7dqwz counterexample refuses tests/test_empty_state_ux.py as an unexpected path and leaves the approved plan, index, and history unchanged; the authorized positive fixture produces an attributed history entry, terminal move, narrowly refreshed index, path-scoped lifecycle commit, and captured pre/post lint outputs; pre-commit failures roll back and a simulated post-commit lint failure reports incomplete without amend/reset.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: CLI tests prove every raw plan-to-terminal alias refuses with one aw ipd finalize next action, while nonterminal plan transitions and non-plan terminal transitions retain behavior; post-transition lint rejects generic or empty actor/summary history and accepts a real agent/model plus summary; CLI help and workflow docs advertise no bypass.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: five focused changes close one observed false-fidelity path from concrete residue through deterministic prevention.

### Execution contract

1. Open questions RESOLVED: OQ-01 (retain and prove the XDG isolation) and OQ-02 (provide no raw terminal-transition escape hatch) are resolved; OQ-03 (retroactive Scope-Paths applicability to already-reviewed pending siblings) and OQ-04 (bootstrap/self-finalize order) MUST be honored as recorded below.
2. Scope fence: touch ONLY `tests/test_empty_state_ux.py`; `agent_workflows/{ipd_schema.py,ipd_lint.py,ipd_authoring.py,status_set.py,cli.py,run_freeze.py}`; one narrowly named new single-IPD lifecycle module if separation is cleaner; focused `tests/test_ipd_*.py`, `tests/test_status_set.py`, and one new lifecycle test file; the implemented IPD lifecycle spec through its managed verb; `.aw/system/workflows/ipd-lifecycle/`; `.aw/records/plans/README.md`; `CONTRIBUTING.md`; CLI/help and generated installer surfaces strictly required for parity. Do NOT touch p7dqwz or any other executed IPD, the pending `execset`/`unifyfileio` plans, unrelated product code, or run-ledger semantics beyond reusing frozen-digest helpers. If implementation needs another surface, STOP and report or amend/re-review this plan before touching it.
3. Honesty rule (hard MUST): when reporting tests or gates passed, paste the ACTUAL runner output and durable receipt path/digest; never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push. Before each commit, compare the intended path list with `git diff --name-only` and leave concurrent user/agent edits untouched.
5. Execute through the authoritative IPD lifecycle. Run pre-execution lint before work; after every E item is performed and every V item independently passes, run pre-transition lint; only then append the attributed workflow-history line, set terminal status, move the plan, create the path-scoped lifecycle commit, run post-transition lint, and report its actual output. BOOTSTRAP / SELF-FINALIZE ORDER (OQ-04, resolved): E-05 removes the raw `aw set executed` plan-terminal path, so this plan cannot rely on it to finalize itself after E-05 lands. Therefore this plan's OWN terminal transition MUST be the FIRST real dogfood of the new `aw ipd finalize` (built in E-04), performed AFTER E-01..E-05 are implemented and all V items pass, and BEFORE relying on any removed path. If `aw ipd finalize` cannot successfully finalize THIS plan (a bug in the just-built finalizer), STOP and report - do NOT fall back to a raw `aw set executed` (E-05 forbids it) and do NOT hand-edit the status to executed; the documented repair path is to fix `finalize` under a new corrective, never to claim a successful execution. The E-02/E-04 code edits themselves are made with the ordinary editor/commit workflow (not via begin/finalize) since the commands do not yet exist; only the final terminal transition dogfoods them.
