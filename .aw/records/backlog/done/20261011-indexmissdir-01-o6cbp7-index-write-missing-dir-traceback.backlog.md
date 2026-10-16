- Id: o6cbp7
- Status: done
- Graduated-To: indexmissdir
- Blocks-Release: next
- Set: indexmissdir
- Priority: low
- Work-Kind: bug
- Summary: aw index prompts and aw index research crash with a FileNotFoundError traceback when the records directory does not exist yet, instead of creating it or refusing with a cannot-run record

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD fbdxmh executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-indexmissdir-01-fbdxmh-refuse-aw-index-write-path-with-cannot-run-when-records-dire.ipd.md); evidence .aw/records/plans/executed/20261014-indexmissdir-01-fbdxmh-refuse-aw-index-write-path-with-cannot-run-when-records-dire.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: fbdxmh
- 2026-10-12 created (aw backlog): filed while authoring sn2svz from 4izduy

MEASURED 2026-10-11 at HEAD 8538be828 while authoring plan sn2svz (from backlog 4izduy). In a fresh 'git init' temp repo with no records tree, 'python3 -m agent_workflows index prompts --agent' and 'index research --agent' both end in 'FileNotFoundError: [Errno 2] No such file or directory: .../records/<type>/INDEX.json' raised from run_index's json_path.write_text, with exit 1 and a Python traceback on stderr and no record on stdout; 'index all --agent' in such a repo dies at the first type that lacks its directory. docs/cli-output-contract.md Section 11.4 forbids this ('Handlers MUST NEVER catch and swallow unexpected exceptions or return exit code 0 on fatal failure' and cannot-run is exit 2 with a kind:error record). Deliberately NOT folded into sn2svz: the fix needs a decision (create the directory, as a first 'aw index' on a fresh install arguably should, versus refuse at exit 2) and it is a human-path defect as much as an agent one. Related: 4izduy, sn2svz.
