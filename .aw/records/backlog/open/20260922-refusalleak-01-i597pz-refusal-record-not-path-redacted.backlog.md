- Id: i597pz
- Status: open
- Blocks-Release: next
- Set: refusalleak
- Priority: medium
- Work-Kind: bug
- Summary: record_refusal writes reason/remedy verbatim into the run summary Diagnostics block without path redaction, unlike its sibling readers integration_refusal_detail and review_integration_refusal_detail which both call _redact_absolute_paths

## Workflow history
- 2026-09-22 created (aw backlog): MEASURED 2026-09-22 during /plan-review of plan 87apfx. render_stream.record_refusal is THE ONE refusal writer and it performs no redaction: reproduced by calling record_refusal with a reason containing an absolute home path and rendering through render_run_summary_table, which printed the path VERBATIM in the Diagnostics block (both the reason line and the remedy line). Its two sibling READERS both redact for exactly this surface: integration_refusal_detail and review_integration_refusal_detail each 'return _redact_absolute_paths(...)', with the docstring reason that the run summary is 'the most-copied output in the product' and AGENTS.md's leak rule forbids machine-identifying strings there. So the leak protection is applied on the legacy-field read path and NOT on the Refusal-record path, which is the newer and now-preferred one (per r2i1b1 F-4, both hosts were moved to record a Refusal rather than rely on the legacy field). SCOPE OF THE FIX: redact at the ONE writer so every refusal code inherits it, rather than at each call site. CAUTION, which is why this is filed rather than fixed inline: record_refusal serves every refusal code in the runner, so a redaction there rewrites messages that were not examined, and mangling an existing operator-facing message is itself a regression in a surface people read mid-incident. A fix should pin the existing messages before and after. Filed from plan 87apfx as finding PR-006/F-9; that plan takes only the bounded obligation that its OWN new facts are relative, proven with aw sanitize --agent.
