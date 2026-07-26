# IPD: Phase 0 conformance harness for host delivery (deterministic scaffolder + operator-run protocol)

- Date: 2026-07-26
- Concern: evidence before delivery - the clean-delta / skills work (D109) is documentation-graded, not reproduced; no delivery tier (skills T2, out-of-repo T1, global T3, excluded-in-repo fallback) may ship until a live per-host/version probe reproduces the documented behavior. This IPD builds the FIRST buildable step: the harness that produces that evidence.
- Scope: build the DETERMINISTIC half of the conformance harness in this repo - a fixture scaffolder (clean temp home + temp git repo + external content + a unique nonce), a per-host command/diagnostic renderer driven by a host matrix, and a results recorder/validator that emits a durable report classifying Resolved vs Followed vs precedence per the research's 9-point recipe. The actual host launches (start OpenCode/Claude Code/Codex/etc., observe the nonce side effect) are the OPERATOR-RUN protocol this tool sets up and records; they are not automated in CI (the hosts are external and not present). Product code + unit tests + docs.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-26 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): Phase 0 of the clean-delta/skills workstream defined by the D109 spec (`.agents/docs/specs/20260726-1239-01-clean-delta-and-tracking-modes.spec.md`, "Build decomposition") and the host-probe reconciliation's 9-point required-release fixture (`.agents/docs/research/20260726-0054-aw-delivery-and-clean-delta-research/20260726-1045-05-external-delivery-host-probe.reconciliation-report.md`). Maintainer decision at authoring: build the deterministic harness (A) now as one IPD; the actual host runs (B) are the operator-run protocol it drives, not CI-automated.

## Goal

Build a deterministic, unit-tested harness that makes a per-host/version delivery probe REPRODUCIBLE and its result RECORDABLE, so no clean-delta/skills tier is ever shipped on documentation alone (D109 gate). The harness: (1) scaffolds an isolated fixture (a clean temp `$HOME`, an empty temp git repo as the "target", and external workflow/skill content OUTSIDE every workspace root) containing a unique nonce and an instruction to create `PROBE-OK-<host>-<version>-<nonce>.txt`; (2) renders, from a per-host matrix, the EXACT commands + diagnostics an operator runs for each tier (T1 out-of-repo pointer, T2 skill, T3 global) plus a conflicting-instruction precedence variant and permission/approval/noninteractive variants; (3) records the operator's observations and VALIDATES them into a durable results report, classifying Resolved (from host diagnostics/context evidence only) vs Followed (only when the exact nonce side effect occurs). The operator step (actually launching each host) is documented and set up by the tool; it is not automated.

Why it matters: the D109 architecture (skills-first delivery, sibling companion repo, etc.) is grounded in reconciled research that is explicitly documentation-graded - "Followed" there means documented, not reproduced. Building any delivery tier on that without a live probe risks shipping a mechanism that silently fails on some host/version. Phase 0 turns the research's per-host claims into a repeatable test whose evidence gates Phases 1-4.

## Project conventions discovered (Step 0)

- Precedent for a workflow-owned, deterministic, unit-tested tool: `.agents/workflows/benchmark/tools/bench_env.py` + `tests/test_bench_env.py` (191 lines). A harness tool can follow the same shape (a Python module with a pure/testable core + a thin CLI).
- The CLI dispatch pattern (`agent_workflows/cli.py`, `sub.add_parser(...)` + `_run_*`) is the home for a new `aw conformance`-style verb if we expose one; alternatively the tool lives under a workflow's `tools/` like `bench_env.py`. Decide at execution (OQ1).
- The per-host command/diagnostic content is DATA from the host-probe reconciliation: the "Preferred T2 layout" table (`...1045-05:498`) and the "T1 host-specific policy" table (`:510`), plus the 9-point required-release fixture (`## Required release fixture`). The renderer consumes a host matrix seeded from these; it does NOT re-derive host behavior.
- Hosts covered by the matrix: OpenCode, Claude Code, Codex, GitHub/VS Code Copilot, Cursor, Antigravity, Gemini CLI (the seven the research evaluated).
- Isolation must not touch the real user environment: a clean temp `$HOME` (never the operator's real `~/.config`, `~/.claude`, `~/.gemini`, etc.) and a temp git repo; the harness NEVER writes to the operator's real host config.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| H1 | HIGH | Medium | maintainer | evidence gate | Every D109 delivery tier is documentation-graded; without a reproducible probe the build phases would ship on unverified host behavior. A deterministic scaffolder + recorder is the gate. | D109 spec "Build decomposition"; host-probe reconciliation "Followed = documented, not reproduced" |
| H2 | MEDIUM | Medium | operator / security | isolation | The probe MUST run against a clean temp `$HOME` + temp repo and MUST NEVER mutate the operator's real host config or home skills dirs; a careless probe could pollute or destroy real user state. | 9-point recipe #1; D109 consent/ownership constraints |
| H3 | MEDIUM | Low | maintainer | resolved-vs-followed discipline | "Resolved" (host loaded/attached the content) and "Followed" (host acted on the nonce) are distinct and must be recorded separately; the recorder must not let a permissive file tool masquerade as host resolution. | host-probe reconciliation Sec on resolution-vs-model-tool behavior |
| H4 | MEDIUM | Low | operator | reproducibility | A result is only trustworthy if the exact host version, settings, fixture tree, commands, logs, and final filesystem state are captured; the report schema must require them. | 9-point recipe #4,#9 |
| H5 | LOW | Low | maintainer | not CI-automatable | The actual host launch cannot run in CI (hosts external, some interactive/consent-gated, some cloud-only). The harness must clearly separate the deterministic (testable-here) machinery from the operator-run step, and NOT fake a host result. | 9-point recipe #7,#8; H5 reasoning |

## Proposed changes (ordered, validatable; checkpointed)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | H2 | Fixture scaffolder: a function/CLI that creates an isolated probe fixture in a caller-supplied temp dir - a clean temp `$HOME`, an empty temp git repo (the "target"), and an external-content dir OUTSIDE the repo - places the tier-specific fixture (a `SKILL.md` for T2; an out-of-repo pointer for T1; a global-location file for T3) carrying a unique nonce and the "create `PROBE-OK-<host>-<version>-<nonce>.txt`" instruction. Pure + parameterized (temp path injected); NEVER touches the real `$HOME`/host config. | new harness module (under a workflow `tools/` or `agent_workflows/`, per OQ1) | Medium | scaffolder builds the fixture tree deterministically in a temp dir; nonce is unique per run; refuses to run against a non-temp/real home; unit-tested with a tmp_path |
| 2 | H1,H3 | Per-host command/diagnostic renderer: from a host matrix (seeded from the reconciliation's T2 layout + T1 policy tables), render the EXACT commands + diagnostic queries an operator runs per host x tier, plus the conflicting-instruction precedence variant and the permission-denied / approval-accepted / noninteractive variants. Output is text an operator executes; the tool does NOT launch hosts. | harness module + a host-matrix data file | Medium | renderer emits per-host/tier command blocks matching the matrix; covers T1/T2/T3 + precedence + permission variants; a host absent from the matrix is reported, not guessed |
| 3 | H3,H4 | Results recorder + validator + report schema: ingest the operator's observations (did the nonce side effect occur? what did the diagnostics show?) and emit a durable results report - a table of host, version, tier, Resolved?, Followed?, how-verified, notes, date, operator, plus the captured settings/fixture/commands/logs/final-state. Validate: Resolved only from diagnostic/context evidence, Followed only from the nonce side effect; refuse to mark Followed without the recorded side effect. | harness module + a results-report template under `.agents/docs/research/` (or `specs/`) | Medium | recorder round-trips observations into the report; validator rejects "Followed" with no side-effect record and "Resolved" with no diagnostic evidence; report has all 9 recipe fields |
| 4 | H1,H2,H3,H5 | Unit tests (the deterministic half): scaffolder builds/refuses-real-home/unique-nonce; renderer per-host/tier output + precedence/permission variants + unknown-host handling; recorder/validator resolved-vs-followed rules + required-field enforcement. Model on `tests/test_bench_env.py`. NO test launches a host. | `tests/test_conformance_harness.py` (new) | Medium | full suite green; the harness's deterministic core is covered; paste ACTUAL output |
| 5 | H5 | Operator PROTOCOL doc: a short runbook telling an operator how to run the probe per host (scaffold -> run the rendered commands in the real host -> record observations -> validate into the report), the resolved-vs-followed rule, the isolation warning (clean temp home only), and that a result gates the corresponding delivery tier. This is the operator-run half (B); it is documentation, not automation. | a doc under `.agents/docs/` (research or a workflow runbook) | Low | protocol doc is concrete + reproducible; states operator-run, isolation, and the tier-gating rule |
| 6 | all | Docs/decision sync: DECISIONS entry (pin at execution) for the Phase 0 harness (deterministic scaffolder/renderer/recorder built + unit-tested; host launch is operator-run; Resolved-vs-Followed discipline; results gate the delivery phases); CHANGELOG; if a CLI verb is added, its `--help`. Cross-reference D109 and the host-probe reconciliation. | `DECISIONS.md`, `CHANGELOG.md`, (optional CLI help) | Low | entries present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| Automating the actual host launches in CI | High | functionality | Hosts are external, some interactive/consent-gated, some cloud-only; CI cannot drive them, and faking a host result would defeat the whole gate (H5). | Operator runs the protocol; results recorded by the tool. |
| Any delivery-tier BUILD (skills packaging, resolver, install, migration) | Medium-High | functionality | Those are D109 Phases 1-4, each its own gated IPD; they consume this harness's evidence. | Per-phase IPDs after Phase 0 evidence exists. |
| Running the probe for all seven hosts as part of this IPD | n/a | operator work | Requires the installed hosts; the IPD is "executed" when the deterministic harness + tests + protocol exist, not when every host is probed. | Operator runs per host/version over time. |

## Scope check

- Over-scope: none - build ONLY the deterministic scaffolder + renderer + recorder/validator + unit tests + the operator protocol doc + a docs note. No host automation, no delivery build.
- Under-scope: MUST isolate to a clean temp `$HOME` + temp repo and NEVER touch the operator's real host config (H2); MUST separate Resolved from Followed and refuse to record Followed without the nonce side effect (H3); MUST require all 9 recipe fields in the report (H4); MUST seed the host matrix from the reconciliation tables (not re-derive host behavior) and report an unknown host rather than guess; MUST clearly mark the host-launch step as operator-run and NOT fake a host result (H5); MUST unit-test the deterministic core (H1-H5) without launching a host.

## Required tests / validation

- Scaffolder: builds the fixture tree in a `tmp_path` (clean temp home + temp repo + external content + tier fixture + unique nonce); refuses to run against a real/non-temp home; two runs produce distinct nonces.
- Renderer: per-host/tier command blocks match the seeded matrix for T1/T2/T3 + the precedence + permission/approval/noninteractive variants; an unknown host is reported, not fabricated.
- Recorder/validator: round-trips operator observations into the report; REJECTS a "Followed" with no recorded side effect and a "Resolved" with no diagnostic evidence; the report carries all 9 recipe fields.
- No test launches or mocks a real host as if it produced a result.
- Full suite `python -m pytest -q` GREEN; paste ACTUAL output. `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- The harness module + tests, the results-report template, the operator protocol doc, DECISIONS, CHANGELOG, and (if added) the CLI verb help. Cross-reference D109 and the host-probe reconciliation.

## Open questions

- OQ1 (tool home + surface): should the harness be an `aw conformance` CLI verb, or a workflow-owned tool under `tools/` (like `bench_env.py`), or both? Lean: a `tools/`-style module with a thin CLI, exposed as an `aw` verb only if that is genuinely useful to an operator. Confirm at review/execution; it does not change the deterministic core.
- OQ2 (report/protocol home): results report + operator protocol under `.agents/docs/research/` (as probe evidence) vs a workflow runbook. Lean: the report is research evidence (research/), the protocol is a short runbook near the tool. Confirm at review.
- OQ3 (host matrix format): a small data file (JSON/TOML) vs in-module constants for the per-host command/diagnostic matrix. Lean: a data file so adding a host/version is data, not code (P8/configurable). Confirm at execution.

## Detailed Implementation Checklist (TODO)

- [ ] **Task 1: Fixture scaffolder**
  - [ ] Add the harness module (home per OQ1) with a `scaffold(...)`-style function taking an injected temp base dir; build clean temp `$HOME` + empty temp git repo + external-content dir + tier fixture (`SKILL.md` / out-of-repo pointer / global file) + unique nonce + the `PROBE-OK-<host>-<version>-<nonce>.txt` instruction.
  - [ ] Guard: refuse to run if the target home is not a temp/isolated dir (never the real `~`).
- [ ] **Task 2: Per-host command/diagnostic renderer**
  - [ ] Add the host matrix (data file per OQ3) seeded from the reconciliation T2-layout + T1-policy tables for the seven hosts.
  - [ ] Render per-host x tier command blocks + precedence variant + permission/approval/noninteractive variants; report (not guess) an unknown host.
- [ ] **Task 3: Results recorder + validator + report schema**
  - [ ] Ingest operator observations; emit the results report with all 9 recipe fields.
  - [ ] Validate: reject `Followed` without a recorded nonce side effect; reject `Resolved` without diagnostic evidence.
- [ ] **Task 4: Unit tests (deterministic half only)**
  - [ ] Add `tests/test_conformance_harness.py` covering scaffolder (build/refuse-real-home/unique-nonce), renderer (per-host/tier + variants + unknown-host), recorder/validator (resolved-vs-followed + required fields).
  - [ ] Run `python -m pytest -q` and PASTE the actual output.
- [ ] **Task 5: Operator protocol doc**
  - [ ] Write the operator runbook (scaffold -> run rendered commands in the real host -> record -> validate), with the isolation warning and the tier-gating rule.
- [ ] **Task 6: Docs / decision sync**
  - [ ] DECISIONS entry (pin the number) + CHANGELOG; cross-reference D109 + the host-probe reconciliation; no em/en dashes.
- [ ] **Task 7: Lifecycle and commit**
  - [ ] Path-scoped commits per checkpoint (`git commit -m msg -- <paths>`; never `git add -A`/`-a`; never push).
  - [ ] Set terminal `Status: executed` and `git mv` this plan to `.agents/plans/executed/`.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. It is Phase 0 of the D109 workstream; Phases 1-4 (delivery build) are separate IPDs gated on the evidence this harness produces.

Completion rule: before claiming done or moving this plan to `executed/`, every `- [ ]` item above MUST be `- [x]` AND independently verified (tests run, actual output pasted); if any item cannot be completed, STOP and report. A ticked box is a claim, not proof.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope (in particular, do NOT automate host launches or build any delivery tier). Never create or push a tag / Release / PyPI upload. The harness MUST NOT mutate the operator's real host config or home; run only against an isolated temp home.

CHECKPOINTED EXECUTION: (1) scaffolder + tests; (2) renderer + host matrix + tests; (3) recorder/validator + report schema + tests; (4) full suite; (5) operator protocol doc; (6) DECISIONS + CHANGELOG. Re-run the full suite at each code checkpoint; pause and report if scope grows toward host automation or a delivery build.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ3.
2. On human approval, execute in checkpoints, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`. Then operators run the protocol per host to produce the evidence that gates D109 Phases 1-4.
