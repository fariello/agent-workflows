# PROPOSAL: re-scope the awoptimize Set into right-sized child IPDs

- Date: 2026-08-21
- Status: PROPOSAL for maintainer review (NOT an IPD; no lifecycle status). Delete or archive after the re-scope executes.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Purpose: show the ENTIRE re-scope transaction on paper before any file moves, per the maintainer's "(b) see the whole map first" instruction.

## Why

The awoptimize Set (Orders 00-08) passed `aw ipd lint` as `conforming` with `Size assessment: standard`,
but several Orders bundle Order-sized, independently-verifiable concerns inside single E-items (e.g. an
append-only tamper-evident ledger, crash recovery, a 12-class evidence-validator suite, whole-catalog
migration). Executing such an Order in one pass risks the exact context/attention degradation the whole
Set exists to prevent. The maintainer chose a FULL split: right-size every remaining tail Order (02-08)
into 2-3 focused children, renumber the tail sequentially (numbering model 1), and reserve the whole
numbering plan up front so numbers do not churn as we split one at a time.

Order 00 (orchestrator) and Order 01 (executed: canonical schema + compiler) are FIXED. Only the
un-executed tail (old Orders 02-08) is re-scoped. A standing backlog item (`8iy2dk`, high, blocks 2.0.0)
adds a right-sizing check to plan-review + IPD-authoring workflows so future Sets are caught at review.

## Reserved numbering plan (final target: Orders 00-18, i.e. 19 Orders)

| New | Title (working) | From (old Order / E-items) | Depends on |
|----:|---|---|---|
| 00 | Orchestrator (re-authored for the 19-Order DAG) | old 00 | - |
| 01 | Canonical workflow schema + compiler (EXECUTED - untouched) | old 01 | - |
| 02 | Ledger + evidence record schemas; requirement freeze | old 02 E-01, E-02 | 01 |
| 03 | Append-only ledger (atomic, hash-chained, crash-safe, corruption-refusing) | old 02 E-03 | 02 |
| 04 | Evidence capture + validators + completion predicates + `aw run` inspection CLI + adversarial tests | old 02 E-04..E-08 | 03 |
| 05 | Runtime state machine + single-writer engine | old 03 E-01, E-02 | 04 |
| 06 | Bounded JIT step packets + outcome envelopes + human decision gates | old 03 E-03, E-04, E-05 | 05 |
| 07 | Retry/correction + resume/cancel/crash recovery + `aw run` lifecycle CLI + model-free simulations | old 03 E-06..E-09 | 06 |
| 08 | Verifier roles + clean verifier packet + verification procedures + corrective routing | old 04 E-01..E-04 | 05, 07 |
| 09 | Isolation hierarchy + concurrency eligibility + merge-and-revalidate + orchestration adversarial tests | old 04 E-05..E-08 | 08 |
| 10 | Capability-evidence registry + isolated positive/negative host probes | old 05 E-01, E-02, E-03 | 05, 08 |
| 11 | Generated skills + host adapters + agy fresh-verifier + host/security tests | old 05 E-04..E-08 | 10 |
| 12 | Benchmark corpus + seeded tasks + adversarial cases + preregistered scoring | old 06 E-01..E-04 | 04, 09 |
| 13 | Runner adapters + ablations + metrics + release thresholds + reports (offline v1) | old 06 E-05..E-09 | 12 |
| 14 | Migration disposition inventory + shared assess/advise family migration | old 07 E-01, E-02, E-03 | 05, 11 |
| 15 | Complex orchestrated workflow migration (release-review, verify-execution, ipd-lifecycle, assess-all, setup-repo, incident/migrate/benchmark) | old 07 E-04..E-07 | 14 |
| 16 | Compact/deterministic workflow migration + generated shims/skills + per-family promotion gates | old 07 E-08, E-09, E-10 | 13, 15 |
| 17 | Compatibility contract + idempotent migration + rollback + deprecation diagnostics | old 08 E-01..E-04 | 16 |
| 18 | Docs + security hardening + lifecycle fixtures + release-readiness review (no publish) | old 08 E-05..E-09 | 17 |

Split summary: 02->3 (02,03,04), 03->3 (05,06,07), 04->2 (08,09), 05->2 (10,11), 06->2 (12,13),
07->3 (14,15,16), 08->2 (17,18). 7 old tail Orders -> 17 new children.

## Per-child E/V scope (what each new Order owns)

Each new child is authored so EVERY E-item is a single observable action an agent can perform +
self-check in one focused pass (the right-sizing bar). Exact E/V ids are assigned by `aw ipd sync`
at scaffold time; the scope below is the authoring intent.

- 02: define the ledger/evidence RECORD schemas (folds in the already-built+committed
  `agent_workflows/run_ledger_schema.py` from old-02 E-01) and the requirement-freeze mechanism
  (bind MUST/scope/validation/output to stable ids + digest; a semantic change makes a new revision
  and invalidates affected evidence).
- 03: the append-only ledger store ALONE (atomic writes, sequence numbers, hash chaining, crash-safe
  recovery, redaction hooks, explicit corruption refusal). This is the safety-critical storage
  substrate; it gets its own Order and its own crash/replay/chain-break adversarial tests.
- 04: evidence capture (provenance envelopes), the evidence validators (one per false-completion
  class), the completion predicates (completion is computed, not claimed), the read-only `aw run
  show|evidence|verify-ledger` inspection CLI, and the adversarial fixtures for the evidence layer.
- 05: the deterministic run state machine + single-writer engine (transition table + authority; two
  concurrent coordinators cannot both act; lock loss fails closed).
- 06: bounded just-in-time step packets + structured outcome envelopes + human decision gates
  (headless `needs_input`, no synthesized consent).
- 07: bounded retry/correction + resume/cancel/crash recovery + the `aw run start|next|record|resume|
  cancel|status|finalize` CLI + model-free simulations of the whole state space.
- 08: role definitions (coordinator/executor/investigator/verifier/corrector/human) + the clean
  verifier packet + verification procedures + corrective-IPD routing.
- 09: portable isolation hierarchy + concurrency eligibility analyzer + merge-and-revalidate gates +
  seeded orchestration adversarial tests (identity collision, leaked summary, worktree conflict...).
- 10: the versioned capability-evidence registry (unverified-by-default) + isolated positive/negative
  host probes. Scoped OpenCode + Codex first; agy 1.1.17 tentative (per prior resolution).
- 11: generated Agent Skills + per-host adapters + the agy fresh-session verifier + generated-parity/
  discovery/permission/security tests.
- 12: benchmark corpus + seeded task repos + adversarial false-completion cases + preregistered
  scoring/stopping rules.
- 13: offline runner adapters + architecture ablations + metrics + release thresholds + reports
  (OFFLINE v1; live multi-model runs are operator-run, per the prior Order-06 resolution).
- 14: the machine-validated disposition inventory for every manifest command/lens/persona + migration
  of the shared assess/advise harness families.
- 15: migration of the complex orchestrated workflows to the runtime/ledger/verifier architecture.
- 16: migration of the compact/deterministic workflows + generated compatibility shims/skills +
  per-family benchmark promotion gates.
- 17: compatibility contract + idempotent migration/update + rollback + opt-in deprecation
  diagnostics.
- 18: operator/author/security docs + threat-model hardening + clean-install/update/rollback lifecycle
  fixtures + a final GO/NO-GO release-readiness review (never tags/publishes/pushes).

## Orchestrator (Order 00) re-authoring

Order 00 currently drives a 9-Order DAG (E-02..E-09 = "execute + validate Order 0X"). Re-scoping to 19
Orders means ~17 "execute + validate child" leaves, which would itself exceed the >18-leaf spirit and
the >5-group threshold if written flat. Proposed restructure: group the children by ARCHITECTURAL LAYER
so the orchestrator stays readable and itself right-sized:

- Layer A - evidence substrate: Orders 02, 03, 04
- Layer B - runtime: Orders 05, 06, 07
- Layer C - verification + isolation: Orders 08, 09
- Layer D - hosts: Orders 10, 11
- Layer E - evaluation: Orders 12, 13
- Layer F - migration: Orders 14, 15, 16
- Layer G - cutover: Orders 17, 18

The orchestrator's E-items become one per LAYER ("drive + integrate layer X, gated on the prior layer")
rather than one per child, with the child table carrying the fine-grained per-Order dependency graph.
That keeps Order 00 at ~7 E-items (right-sized) while still coordinating 17 children. The orchestrator's
Completion criteria, Cross-IPD validation, and Risk register are updated to the 19-Order shape. Because
its meaning changes materially, Order 00 goes back through review + human sign-off.

## The re-scope transaction (what I will do on approval)

1. Retire old Orders 02-08: prepend `RETIRED 2026-08-21: superseded by awoptimize re-scope (see this
   proposal); resplit into Orders 02-18` and `git mv` each to `.aw/records/plans/superseded/`.
   (Old 02's already-committed product code, `run_ledger_schema.py`, STAYS; it belongs to new Order 02.)
2. Scaffold new Orders 02-18 via `aw ipd scaffold` (correct clustering names), `aw ipd sync` for E/V ids
   and validation skeletons. Author each child's E-items to the one-concern bar above.
3. Re-author Order 00 to the layer-grouped 19-Order DAG.
4. `aw plans index` to regenerate the manifest.
5. Then, one Order at a time (discuss -> execute -> verify -> transition), starting with new Order 02.

## Open decisions for the maintainer

1. Approve this numbering + split map as the plan of record?
2. Approve the layer-grouped orchestrator restructure (Order 00 E-items per layer, not per child)?
3. Titles above are working titles; any you want changed before scaffolding?
4. After scaffolding, the new Orders are unapproved; execution waits for your sign-off per Order (or per
   layer, if you prefer to approve a layer at a time).
