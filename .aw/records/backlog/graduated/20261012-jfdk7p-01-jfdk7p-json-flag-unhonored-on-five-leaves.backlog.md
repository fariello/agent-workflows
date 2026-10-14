- Id: jfdk7p
- Status: graduated
- Graduated-To: jfdk7p
- Blocks-Release: next
- Set: jfdk7p
- Priority: medium
- Work-Kind: bug
- Summary: Five leaves advertising the shared --json flag emit no parseable JSON on stdout: config get and config is print FAIL prose on exit 2, upgrade-test env and probe write zero stdout bytes, upgrade-test clean prints 'Nothing to clean.'

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: pirm70
- 2026-10-12 created (aw backlog): Found authoring cgsrnb (backlog uxq5mg) at HEAD 85184f648 by running every swept conformance leaf with --json and json.loads on stdout. Measured: 'config get interactive --json' rc=2 stdout 'FAIL Unknown config key ...' (the --agent spelling emits a kind:error record); 'config is interactive --json' rc=2 stdout 'FAIL Missing variable name ...'; 'upgrade-test env dummy --json' and 'upgrade-test probe dummy --json' rc=2 with 0 stdout bytes and 'error: not a sandbox' on stderr (the --agent spelling emits a kind:error record); 'upgrade-test clean --json' in an isolated installed project rc=0 stdout 'Nothing to clean.'. Same defect class as xym8g8: the flag is declared on the shared common parent, appears in --help, and is silently not honored, so a parsing caller gets a json.loads error or an empty string. Bug under the user-perceptible test for the same reason xym8g8 was; gated next per policy. cgsrnb registers these as known_broken in its new gate citing this item.
