- Id: mmpjti
- Status: done
- Graduated-To: mmpjti
- Blocks-Release: next
- Set: mmpjti
- Priority: low
- Work-Kind: bug
- Summary: handler-level early refusals in backlog new, specs new, prompts new and ipd scaffold still emit no aw.agent/v1 record under --agent

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD xvv7n4 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-mmpjti-01-xvv7n4-emit-aw-agent-v1-cannot-run-records-on-remaining-handler-usa.ipd.md); evidence .aw/records/plans/executed/20261014-mmpjti-01-xvv7n4-emit-aw-agent-v1-cannot-run-records-on-remaining-handler-usa.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: xvv7n4
- 2026-10-12 created (aw backlog): handler-level early refusals in backlog new, specs new, prompts new and ipd scaffold still emit no aw.agent/v1 record under --agent

Measured at HEAD 2a22b4ae2 while authoring plan 0z7ds3 (from backlog 91pjax). Plan 0z7ds3 fixes the argparse-level refusal path CLI-wide and the four MISSING-REQUIRED handler refusals that the vfv2db mutation sweep hits (backlog new --priority/--work-kind and --summary, specs new --title, prompts new --slug). It deliberately does NOT convert the OTHER early refusals in the same handlers, which remain silent or non-JSON under --agent: (1) aw specs new --title x --date bad --agent exits 2 with 0 stdout bytes; (2) aw backlog new --priority low --work-kind bug --summary 'bad<newline>summary' --agent exits 2 with empty stdout, and tests/test_backlog_descriptive_safety.py test_agent_mode_refusal_shape currently PINS out == '' for that case, so the fix must change that assertion; (3) aw ipd scaffold --kind child --title '' --set x --order 1 --priority low --work-kind bug --agent prints the human line 'error: --title is required' to STDOUT, which is neither empty nor a valid record (ipd_authoring.run_scaffold uses print, not stderr). The remedy is to route each through the shared refusal emitter 0z7ds3 introduces (renderers.emit_usage_refusal). Gate a complete fix with a behavioral sweep that drives each refusal branch under --agent rather than a hand list.
