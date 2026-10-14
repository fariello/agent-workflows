- Id: aavf6a
- Status: graduated
- Graduated-To: idxjsonroot
- Blocks-Release: next
- Set: idxjsonroot
- Priority: low
- Work-Kind: bug
- Summary: aw index <type> --check --json puts the absolute repository path in data.repo_root, which the output contract forbids a producer to do without an approved spec

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: 7dcpe1
- 2026-10-12 created (aw backlog): filed while authoring sn2svz from 4izduy

MEASURED 2026-10-11 at HEAD 8538be828 while authoring plan sn2svz. 'python3 -m agent_workflows index plans --check --json' emits a document whose data object is {target, repo_root, human_rendered} with repo_root set to the ABSOLUTE checkout path (a home path on the maintainer's machine). The value comes from artifact_core.emit_index_check_result, which stores str(repo_root) in CommandResult.data (comment: 'repo_root must be a str, never a Path'), and JsonRenderer passes data through unredacted. docs/cli-output-contract.md Section 4 'Path Sanitization and Leak Posture' exempts data from DOWNSTREAM redaction but states 'The data exemption is an exemption from downstream redaction and not a licence for a producer to put an absolute path there: a command-specific payload must itself carry repo-relative text unless an approved spec requires otherwise'; no spec requires it here. The value is also used internally by Diagnostic.to_dict to relativize locations, so the fix must keep that working (for example pass repo_root out of band) rather than just deleting the key. Plan sn2svz's new WRITE-path helper deliberately does NOT copy this pattern; the --check path it leaves untouched is this item. Related: 4izduy, sn2svz, n9ua3b.
