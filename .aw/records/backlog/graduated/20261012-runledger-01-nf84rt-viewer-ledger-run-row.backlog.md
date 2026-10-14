- Id: nf84rt
- Status: graduated
- Graduated-To: runledger
- Set: runledger
- Priority: low
- Work-Kind: followup
- Summary: aw runs viewer lists a ledger-only run directory as a driver run with '0 steps', once aw run init (plan v47z9u) creates one under the runs root

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 3a3hh9
- 2026-10-12 created (aw backlog): Filed while authoring plan v47z9u from backlog hegwri: measured the viewer row for a ledger-only run dir.

MEASURED 2026-10-12 at HEAD a3084a234 in lane worktree hegwri: with a conformant kind=run header appended at state_root(repo)/run-abcdef1234/ledger.jsonl in a scratch git repo, bare 'aw runs' printed the row 'run-abcdef1234' followed by '  0 steps: 0 steps'. run_viewer.discover_run_dirs admits every 'run-*' directory under state_root, and the viewer then renders it with the driver-run model (state.json absent). After plan v47z9u ships aw run init writing exactly there, every ledger run will appear this way. Options: classify a ledger-only directory and render it with the ledger model (run_cli already reconstructs it), or skip it in the driver viewer and point at 'aw runs status'. Not a v47z9u item because run_viewer is a separate surface with its own contract. Depends on v47z9u being executed.
