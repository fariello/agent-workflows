- Id: vcqobe
- Status: graduated
- Graduated-To: promptidxword
- Blocks-Release: next
- Set: promptidxword
- Priority: low
- Work-Kind: bug
- Summary: aw index prompts prints 'wrote INDEX.json' and 'wrote INDEX.md' on every run, including when neither file changed, unlike plans and research which say 'up to date'

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: whri6h
- 2026-10-12 created (aw backlog): filed while authoring sn2svz from 4izduy

MEASURED 2026-10-11 at HEAD 8538be828 while authoring plan sn2svz. prompts_index.run_index compares the new INDEX.json/INDEX.md against disk (json_changed/md_changed) and skips the write when unchanged, but its human print path ignores both flags and prints 'wrote INDEX.json (N prompts)' then 'wrote INDEX.md' unconditionally; running 'python3 -m agent_workflows index prompts' twice in a row prints 'wrote' both times. plans_index.run_index and research_index.run_index print 'up to date' in that case. A human therefore cannot tell from the output whether anything was written. Plan sn2svz fixes the MACHINE surfaces (--agent/--json) of this verb and deliberately keeps every HUMAN line byte-identical, so this human-path wording defect is out of its scope. Related: 4izduy, sn2svz.
