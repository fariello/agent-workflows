# IPD: Package gemini-quota and add opt-in aw install more with discovery tip

- Date: 2026-11-17
- Kind: orchestrator
- Concern: Make `gemini-quota` part of `agent-workflows`, installed after asking via `aw install more`, and advertise `aw install more` from `aw install`.
- Scope: Orchestration only: sequence the two child plans below (`z403j4` Order 01 and `58isyp` Order 02) in dependency order and confirm each reaches `executed`. No code, test, or record work of its own.
- Scope-Paths: .aw/records/plans/pending/20261117-installmore-00-5qqgfb-package-gemini-quota-and-add-opt-in-aw-install-more-with-dis.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: pass
- Coverage-Fingerprint: 33886112ea5b9b0d69b4219282c1044340fc8d9ec073ecc21220a2727edee576
- Coverage-Checked: 2026-11-18 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Short-Description: Integrate gemini-quota into agent_workflows, install optional extras with consent via aw install more, and announce aw install more from aw install
- Work-Kind: feature
- Priority: medium
- Set: installmore
- Order: 0
- Highest E allocated: 02
- Author: antigravity
- Id: 5qqgfb

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-18 to-review (aw set): status set to to-review
- 2026-11-18 coverage pass (aw oc run): fingerprint 33886112ea5b, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-18 coverage pass (aw oc run): fingerprint 913513f30092, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-18 coverage pass (aw oc run): fingerprint beaa9d973f58, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-18 draft (antigravity): created and authored orchestrator for Set `installmore`.

## Goal

Coordinate packaging `gemini-quota` inside `agent_workflows` and wiring `aw install more` plus its `aw install` discovery tip across two sequenced child plans.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Child sequencing

- [ ] E-01 CONFIRM z403j4 REACHED executed
  - Depends on: none
  - Expected outcome: `20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md` (Order 01) is in `.aw/records/plans/executed/` with `Status: executed`, providing `agent_workflows/gemini_quota.py` and `tests/test_gemini_quota.py`.
  - Execution state: pending

- [ ] E-02 CONFIRM 58isyp REACHED executed
  - Depends on: E-01
  - Expected outcome: `20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md` (Order 02) is in `.aw/records/plans/executed/` with `Status: executed`, providing `aw install more`, the opt-in prompt, the `aw install` discovery tip, docs, and tests.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `z403j4` | `20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md` | Package `gemini-quota` into `agent_workflows/gemini_quota.py` with stdlib-only dependencies and behavioral tests in `tests/test_gemini_quota.py` | none |
| 02 | `58isyp` | `20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md` | Add extensible `install_more` catalog and ask-first `aw install more` command, emit `aw install more` tip after `aw install`, update docs, and run full verification | Order 01 |

## Completion criteria (the whole Set is done only when)

- `agent_workflows/gemini_quota.py` runs standalone (`python3 -m agent_workflows.gemini_quota --help`) and passes `tests/test_gemini_quota.py` (`aw check-local-leaks` clean). Owner: `z403j4`
- `aw install more` presents available extras (`gemini-quota`), prompts before writing, installs executable launchers under `--bin-dir` / `$XDG_BIN_HOME` / `~/.local/bin`, `aw install` displays the discovery tip once per run when uninstalled extras remain, and `tests/test_install_more.py` + `tests/test_command_surface_declarations.py` + `tests/test_exit_contract_conformance.py` + `README.md` are updated and verified. Owner: `58isyp`

## Cross-IPD validation

- Whole-Set integration, CLI contract conformance, leak checking, and full core pytest verification across both modules are performed by `58isyp` (Order 02) after `z403j4` lands. Owner: `58isyp`

## Deferred / out of scope (with reason)

- Unattended default installation without user consent, dotfile RC modification, and additional extras beyond `gemini-quota`: handled or explicitly deferred by `58isyp`.

## Scope check

- Over-scope: none.
- Under-scope: none. All implementation, wiring, documentation, and cross-module validation are owned by `z403j4` and `58isyp`.

## Required tests / validation

- This orchestrator runs no tests of its own; child validation is executed by `z403j4` (`tests/test_gemini_quota.py`, core suite) and `58isyp` (`tests/test_install_more.py`, `tests/test_gemini_quota.py`, `tests/test_command_surface_declarations.py`, `tests/test_exit_contract_conformance.py`, core suite).

## Open questions

None; resolved inside `z403j4` (Order 01) and `58isyp` (Order 02).

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans z403j4` confirming `20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md` is in `.aw/records/plans/executed/` with `Status: executed`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans 58isyp` confirming `20261117-installmore-02-58isyp-add-aw-install-more-opt-in-companion-installer-and-discovery.ipd.md` is in `.aw/records/plans/executed/` with `Status: executed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Sequence execution as `z403j4` -> `58isyp`; once both children reach `executed` on disk, retire `5qqgfb` cleanly via `aw ipd finalize` or automated runner retirement.
