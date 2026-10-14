- Id: aws1tg
- Status: graduated
- Graduated-To: aws1tg
- Blocks-Release: next
- Set: aws1tg
- Priority: medium
- Work-Kind: bug
- Summary: Nine leaves ignore the shared --fields projection under --agent and emit unrequested keys: ipd coverage, partition, oc update-models, storage reattach, and upgrade-test env, list, probe, sandboxes and clean

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 83ns86
- 2026-10-12 created (aw backlog): Found authoring cgsrnb (backlog uxq5mg) at HEAD 85184f648 by running every swept conformance leaf with '--agent --fields cmd' and collecting terminal-record keys outside agent_schema._PRESERVED_FIELDS. Measured unrequested keys: ipd coverage [detail, summary]; partition [commands, cycles, shards, split_components]; upgrade-test env/list/probe/sandboxes/clean [findings]; oc update-models [findings]; storage reattach [findings]. Same defect class as the --fields half of xym8g8: the flag is declared on the shared common parent and these records bypass agent_schema.filter_record_fields. Bug: docs/cli-output-contract.md Section 6 promises the projection and the caller pays for unrequested tokens; gated next per policy. cgsrnb registers these as known_broken in its new gate citing this item.
