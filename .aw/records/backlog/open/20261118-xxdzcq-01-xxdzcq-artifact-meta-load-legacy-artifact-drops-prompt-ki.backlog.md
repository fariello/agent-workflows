- Id: xxdzcq
- Status: open
- Set: xxdzcq
- Work-Kind: bug
- Priority: medium
- Summary: artifact_meta.load_legacy_artifact drops prompt_kind and created_day when reading prompt records
- Short-Description: artifact_meta.load_legacy_artifact drops prompt_kind and created_day when reading prompt records
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-18 created (aw backlog): artifact_meta.load_legacy_artifact drops prompt_kind and created_day when reading prompt records

Observed: reading a staged prompt created via artifact_meta.create (or aw prompts new) with artifact_meta.read(<id6>) returns fields['prompt_kind'] = None and fields['created_day'] = None, even though the file's <!-- aw-prompt: ... --> metadata header contains Kind: and Created:. Cause: in agent_workflows/artifact_meta.py::load_legacy_artifact, field_map maps 'Kind' unconditionally to 'plan_role' (which is absent from REGISTRY['prompt']) and has no mapping for 'Created' on prompts (so bk.lower() becomes 'created' rather than 'created_day'). Fix: map 'Kind' -> 'prompt_kind' and 'Created' -> 'created_day' when art_type == 'prompt', preserving existing behavior for other record types.
