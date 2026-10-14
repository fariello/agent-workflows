- Id: 2ohbkj
- Status: graduated
- Graduated-To: 2ohbkj
- Set: 2ohbkj
- Priority: low
- Work-Kind: followup
- Summary: Restore behavioral tests that a bare stop/audit first token is not rewritten into start in both runner drivers

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: aka0li
- 2026-10-12 created (aw backlog): Restore behavioral tests that a bare stop/audit first token is not rewritten into start in both runner drivers

Measured 2026-10-11 while authoring plan 65d5zf (backlog 3tov52): the implicit-start shim in oc_runipd.main and agy_runipd.main must list stop/integrate/audit so e.g. `stop <run-id> --now` is not rewritten into `start stop ...` (which would LAUNCH a run). The behavioral guards (tests/test_runner_stop_triggers.py::_stop_is_not_rewritten, which called module.main(['stop', ...]) and asserted no run dir was created) were deleted with the whole file in 19313eed7. `rg -n 'main\(\["(stop|audit)"' tests/` finds nothing today; integrate is still exercised through main(). Restore BEHAVIORAL coverage (drive main, assert no run dir / correct routing) for stop and audit on both hosts. Do NOT restore the AST/regex _shim_set pin (P16).
