---
id: 40g511
created: 20260826
set: aw-run-spec-build-order
order: 00
topic: [runner, dependencies, build-order, agentadhere, awoptimize]
model:
kind: findings
status: intake
outcome: adopted
summary: What exists vs net-new for the aw run deterministic run-and-verify spec (25kzda): build-order dependency map
consumed-by: [25kzda]
---

# Build-order map: `aw <host> run` spec (25kzda) vs. the existing codebase

Companion to spec `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`
(id `25kzda`). Verdicts are evidence-backed from a code sweep on 2026-08-26. Purpose: sequence the
IPD Set(s) that implement the spec, reusing what exists instead of rebuilding it.

## The central finding

There are TWO disconnected execution systems in the tree, and the spec's whole thesis is that they
become one:

1. **The `awoptimize` library layer** (built by the executed `awoptimize` + `execset` + `ipdgates`
   Sets): `run_ledger_schema.py`, `run_ledger_store.py`, `run_freeze.py`, `run_packet.py`,
   `run_evidence.py`, `verify_roles.py`, `host_capability_registry.py`, `worktree_lease.py`,
   `security_hardening.py`, surfaced by the top-level `aw run {show,evidence,verify-ledger,start,
   next,record,...}` verb. Rich, tested, hash-chained, role-separated machinery.
2. **The actual runner drivers** `oc_runipd.py` / `agy_runipd.py`, surfaced as `aw oc run` /
   `aw agy run` (aliases of `runipd`). These are what a user invokes. They import NONE of layer 1
   (confirmed: `oc_runipd.py` imports only stdlib), keep their own `state.json` + plain jsonl events,
   and steer the agent with RUNBOOK PROSE ("commit path-scoped, never push"), not engine enforcement.

**Therefore the load-bearing prerequisite for most of the spec is WIRING layer 1 into layer 2, not
greenfield construction.** The spec reads as mostly net-new; the code says most of the hard parts are
built but unconnected.

## Capability-by-capability verdict

| # | Spec capability | Verdict | Evidence / gap |
|---|---|---|---|
| 1 | `aw <host> run` per-type/per-status dispatch | PARTIAL | `aw oc/agy run` are aliases of `runipd` (cli.py:2202,2221) dispatching `{start,resume,status,report}`. `determine_action()` (oc_runipd.py:845) is IPD-only, two-way (review/execute). `--full-auto` exists (oc_runipd.py:932) but writes real `approved`, NOT the spec's `auto-approved`. No `--allow-mixed`/`--unattended`/`--allow-unverifiable`/`--action`. No spec/backlog/prompt dispatch, no status table. |
| 2 | Selector union + mixed-type gate | PARTIAL | `selectors.resolve()` has the exact precedence + unique-kind collision policy the spec wants, but resolves ONE record_type at a time. No cross-type `--type` union, no `SELECTOR-TYPE-CONFLICT`, no mixed-type gate (`run mixed`: zero matches). `all`=IPD-only lives in `oc_runipd.expand_selectors` (line 682), bypassing selectors.py. |
| 3 | Hash-chained run ledger + `aw runs` surface | PARTIAL | `run_ledger_store.py` fully implements append-only, single-writer (fcntl), SHA-256 hash-chained ledger, fail-closed (`BrokenChainError`, `verify_chain`:432, `prev_hash`/GENESIS). Full typed record vocab in `run_ledger_schema.py`. Surface is `aw run show/evidence/verify-ledger` (singular `run`, not `runs`; `verify-ledger` not `verify`). MISSING: `AW-Run:`/`AW-Item:` commit trailers (zero matches). NOT wired to oc/agy drivers. |
| 4 | Freeze / bounded packet / evidence capture | EXISTS (libs) | `run_freeze.py` (requirement freeze, stable id+digest, semantic-vs-cosmetic). `run_packet.py` (bounded JIT packets, scope fence, allowed tools/files, packet digest, size budget). `run_evidence.py` (provenance envelopes, 13 false-completion validators, deterministic `evaluate_completion`). Gap: not driven by the runner; freeze bundle lacks the spec's dependency-requirements + required-host-capabilities additions. |
| 5 | Per-host capability descriptor + fail-closed (A4) | PARTIAL (wrong axis) | `host_capability_registry.py` has unverified-default, TTL/expiry, fail-closed status vocab, 9 negative-probe classes - but those are a DIFFERENT axis (missing_skill, denied_permission, ...). The spec's execution-safety classes (deny_push, commit_gateway, hook_preserving, isolated_worktree, fresh_session) are NOT present (zero matches). Fail-closed machinery exists; the needed capability set does not. |
| 6 | Skeptical verifier / role separation | EXISTS | `verify_roles.py`: role contracts, executor-cannot-verify-own-work, clean verifier packet excluding executor prose, corrective routing. `agy_verifier.run_fresh_verifier` (line 142). Gap: `oc_runipd` audit turn is prose-runbook driven, not this module. |
| 7 | Commit gateway + no-push + hooks + worktree isolation (A1 containment) | PARTIAL / NET-NEW | `worktree_lease.py` EXISTS (real `git worktree`, per-path exclusive leases, gitignored `.aw/worktrees/`). BUT no engine-owned commit gateway: oc/agy drivers INSTRUCT the agent via prose to `git commit -- <path>` / "never push" (oc_runipd.py:871,940,1184); the agent runs git itself. No `--no-verify` interception, no host-enforced no-push. `ipd finalize` makes an engine-owned path-scoped LIFECYCLE commit, but that is the terminal move, not executor-work containment. |
| 8 | `Item-Dependencies` (cross-item, id6-grounded, mandatory) | NET-NEW | Zero matches. `ipd_schema.META_RECOGNIZED` (line 173) has no dependency field. Existing `Depends on:` (`parse_depends_on`:504) is the intra-plan E-* field the spec explicitly distinguishes. No `aw ipd dependencies` verb, no cross-IPD graph builder, no `check.ipd-dependency-*` rule. Entirely greenfield. |
| 9 | `From-Spec` field + setter + check | NET-NEW | Absent from `META_RECOGNIZED`; no setter; no cross-tree check. `From-Backlog` (ipd_schema.py:171) is the exact template to clone. |
| 10 | Prompt `Run contract` block | NET-NEW | Zero matches for `Run contract`/`Check-Recipes`/`Change-Policy`/`Expected-Paths`. No prompt-contract parsing exists. |
| 11 | `aw check --format json` policy engine, rich findings | PARTIAL | `check_engine.py` `CloseVerdict` (line 707: legitimate/severity/reason/fixes/path, ok/warn/error + recovery `fixes`) is the SHAPE the spec wants, but scoped to release-gate/backlog close-legitimacy + a few from-backlog rules. Not a general rule-ID engine. `aw check` has `--json`/`--agent` but NO `--format json` with the spec's finding vocab. The versioned policy schema is PLANNED in pending `agentadhere-02` (uisjns). |
| 12 | Phased IPD lint | EXISTS | `aw ipd lint --phase` supports author, review-finalize, pre-execution, pre-transition, post-transition. Spec's "review-readiness" ~= existing "review-finalize" (naming reconcile). Machinery complete. |
| 13 | Terminal transaction / begin + finalize + scope reconciliation | EXISTS | `aw ipd begin` (cli.py:994): pre-execution lint, freezes requirements+Scope-Paths+base HEAD into gitignored `.aw/state/` receipt, fail-closed on dirty/ambiguous baseline. `aw ipd finalize` (cli.py:1022): validates receipt, pre-transition lint, compares changed-vs-Scope-Paths (refuses unexplained/collision), attributed history, terminal status+move, path-scoped lifecycle commit, post-transition lint, `--scope-reason`/`--scope-ack`. This IS the spec's begin-receipt/scope/terminal-transaction for a single IPD. |
| 14 | Draft-readiness nudge (fleshed-out draft -> to-review) | NET-NEW (planned) | No detect-and-nudge check exists. Scoped in pending, unexecuted `agentadhere-02` (uisjns). |

## Mostly-done (strong reuse targets)

Ledger+schema+`aw run` surface (#3, minus trailers/wiring); freeze/packet/evidence + completion
predicate (#4); role-separated fresh verifier (#6); worktree isolation + leases (part of #7); phased
lint (#12); `ipd begin`/`finalize` with baseline freeze + scope reconciliation for a single IPD (#13).

## Mostly-greenfield (the spec's load-bearing net-new)

Unified per-type/per-status dispatcher (#1); cross-type selector union + mixed-type gate (#2); the
ENTIRE cross-item dependency system (#8); `From-Spec` (#9); prompt `Run contract` (#10); general
`aw check --format json` rule engine (#11, planned in agentadhere); draft-readiness nudge (#14,
planned in agentadhere); execution-safety capability CLASSES on the descriptor (#5); the engine-owned
commit gateway + host-enforced no-push/hooks (#7).

## Proposed build order (dependency-sequenced)

Root insight: WIRE, then EXTEND, then add the truly-new graph/contract layers.

- **Phase R0 - Runner rename + wiring foundation.** Complete the `runipd/runagy -> aw <host> run`
  consolidation (the separate rename decision), and make the oc/agy drivers CONSUME the awoptimize
  libraries (ledger, freeze, packet, evidence, verify_roles) instead of prose + local state.json.
  This is the single highest-leverage prerequisite; #1,#3,#4,#6 all unblock from it. Overlaps the
  `runnernorm` Set (reconcile it).
- **Phase R1 - Engine-owned commit gateway + capability classes (#5,#7).** Add the execution-safety
  capability classes to `host_capability_registry` (deny_push/commit_gateway/hook_preserving/
  isolated_worktree/fresh_session) and an engine commit gateway that path-scopes + refuses push/
  `--no-verify`, replacing the runbook-prose promises. Reuses `worktree_lease` + `security_hardening`.
  Fail-closed per A4. Enables A1 containment.
- **Phase R2 - Policy engine + draft-readiness (#11,#14).** Land `agentadhere` phases 0-1 (invariant
  catalog + versioned `aw check --format json` rule engine + draft-readiness nudge). The dispatcher
  and all checklists depend on this finding shape. THIS SET ALREADY EXISTS PENDING (agentadhere-01/02)
  - reconcile, do not duplicate.
- **Phase R3 - Cross-item dependency system (#8) + From-Spec (#9).** `Item-Dependencies` schema field
  + `aw ipd dependencies set` + shared graph predicate + `check.ipd-dependency-*` family + opt-in
  commit hook + runner preflight, mirroring the bklggrad From-Backlog one-predicate-many-surfaces
  model. Add `From-Spec` (clone From-Backlog). Depends on R2's rule engine.
- **Phase R4 - Unified dispatcher + selector union + mixed-type gate (#1,#2).** Per-type/per-status
  dispatch, cross-type selector union, `all`=IPD default, mixed-type gate, `auto-approved` (not
  `approved`) for `--full-auto`. Depends on R0 (wiring), R2 (checker), R3 (dependency preflight).
- **Phase R5 - Prompt Run contract (#10) + commit trailers (#3) + `aw runs` naming.** Prompt contract
  parsing/verification; `AW-Run:`/`AW-Item:` commit trailers so run-owned commits are findable;
  reconcile the `aw run` vs spec's `aw runs` surface naming.

## Overlaps to reconcile (do NOT duplicate)

- `agentadhere` (pending): phases 0-5 already stake out the policy schema / `aw check --format json` /
  atomic primitives / event-derived scope / draft-readiness (spec #11,#14, part of #7). R2/R1 must be
  reconciled INTO agentadhere, not re-planned.
- `bklggrad` (executing): the From-Backlog one-predicate-many-surfaces model is the exact template for
  #8/#9 (R3).
- `runnernorm` (pending): its runipd render-extraction + tool graduation overlaps R0; reconcile with
  the runner rename.
- `awoptimize`/`execset`/`ipdgates` (executed): the reuse targets; R0 is "connect to these."
