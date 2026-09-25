- Id: n8akr5
- Status: done
- Set: n8akr5
- Priority: medium
- Work-Kind: bug
- Summary: migrate test_orchestrator_probe BothHostsActuallyRefuse fixtures to typed orchestrator row grammar

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by b165ba2d; file later removed in 19313eed
- 2026-09-24 created (aw backlog): migrate test_orchestrator_probe BothHostsActuallyRefuse fixtures to typed orchestrator row grammar

## Problem

`tests/test_orchestrator_probe.py::BothHostsActuallyRefuse` embeds synthetic fixtures `PARENT_ONLY_WORK` and `ORCHESTRATION_ONLY` with pre-orchtyped prose `E-*` rows (`- [ ] E-01 SEQUENCE THE CHILDREN IN ORDER...`). When `0xmk4e` wires `enforce_orchestrator_shape_gate` ahead of the probe gate in `initialize_run_core`, `initialize_run` correctly refuses those fixtures under `IPD-S407` before reaching the probe, causing `BothHostsActuallyRefuse` in `test_orchestrator_probe.py` (which asserts probe-level refusals and probe skip messages) to fail until its fixtures are migrated.

## Remediation

In child 04/05 migration or follow-up, migrate `BothHostsActuallyRefuse`'s embedded fixtures to use typed child-tracking rows (`CONFIRM <id6> REACHED <status>`) with bare indented continuation lines for the uncovered work case.
