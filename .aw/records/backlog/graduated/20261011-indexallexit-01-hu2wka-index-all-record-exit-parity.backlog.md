- Id: hu2wka
- Status: graduated
- Graduated-To: indexallexit
- Blocks-Release: next
- Set: indexallexit
- Priority: low
- Work-Kind: bug
- Summary: aw index all --agent and aw index all --check --agent emit one record per type whose exit fields disagree with the process exit code

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 7i4zba
- 2026-10-12 created (aw backlog): filed while authoring sn2svz from 4izduy

MEASURED 2026-10-11 at HEAD 8538be828 while authoring plan sn2svz. 'python3 -m agent_workflows index all --check --agent' in this repository prints three result records (plans exit 0, prompts exit 0, research exit 1) and the process exits 1, because cli._run_noun_verb loops the types, lets each backend emit its own record, and returns max(rc). docs/cli-output-contract.md Section 4 'Exit Code Parity' requires 'The embedded exit field in every record MUST equal the process exit code', so two of the three records violate it, and a consumer reading the FIRST record (rather than the last) sees exit 0 for a failing run. Plan sn2svz converts the per-type WRITE path to one record per type and so inherits this multi-record shape for 'index all' without the write path; it deliberately does not redesign the 'all' aggregation, which needs a decision (one aggregate record with per-type data, versus an item stream plus a terminal summary) shared by both the --check and write paths. Related: 4izduy, sn2svz, n9ua3b.
