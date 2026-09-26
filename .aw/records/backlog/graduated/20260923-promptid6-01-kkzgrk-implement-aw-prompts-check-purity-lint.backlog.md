- Id: kkzgrk
- Status: graduated
- Graduated-To: promptlint
- Set: promptid6
- Priority: medium
- Work-Kind: feature
- Summary: aw prompts check (the purity lint approved spec 20260808-1958-01-prompt-purity-lint specifies) is not implemented, so nothing mechanically guards prompt purity

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set promptlint (commit 2c7068ca).
- 2026-09-23 created (aw backlog): aw prompts check (the purity lint approved spec 20260808-1958-01-prompt-purity-lint specifies) is not implemented, so nothing mechanically guards prompt purity

FOUND WHILE EXECUTING IPD ubac5n (promptid6), which had to demonstrate a purity property by inspecting file contents because no lint exists to cite.

WHAT IS WRONG: approved spec .aw/records/specs/20260808-1958-01-prompt-purity-lint.spec.md specifies a prompt-purity lint. Measured 2026-09-23: 'aw prompts check' exits 2 with "invalid choice: 'check' (choose from 'new')". The spec is therefore UNIMPLEMENTED and the contract it defines (exactly one leading '<!-- aw-prompt: ... -->' line, no YAML front matter, no body boilerplate, nothing else before the prompt body) has no mechanical enforcement.

WHERE: agent_workflows/prompts.py (no run_check), agent_workflows/cli.py prompts_sub (only 'new' is registered), check_engine.SUPPORTED['prompts'] == ('names',) so only the FILENAME is checked.

WHY IT MATTERS, CONCRETELY: ubac5n found and repaired a live defect that wrote a '- Id:' bullet into a prompt BODY via 'aw rename prompts --to-id6'. That defect had shipped and was invisible precisely because this lint does not exist; it was caught by reading the spec and simulating the write, not by a check. A recurrence of the same class would be equally invisible.

ubac5n DELIBERATELY EXCLUDED THIS (see its 'Deferred / out of scope'): folding a new lint into a naming migration would make one review cover two deliverables.

NOTE the spec's own status should be reconciled when this is built: it is approved but unimplemented, and an agent may not set 'implemented' without cited evidence.
