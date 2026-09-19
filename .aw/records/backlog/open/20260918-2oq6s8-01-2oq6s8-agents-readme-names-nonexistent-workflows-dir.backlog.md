- Id: 2oq6s8
- Status: open
- Blocks-Release: next
- Set: 2oq6s8
- Priority: medium
- Work-Kind: bug
- Summary: The shipped agents-README.md template describes a records/workflows/ dir that no install creates

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): The shipped agents-README.md template describes a records/workflows/ dir that no install creates

MEASURED 2026-09-18 while executing wfartifacts Order 04 (l1c1iz).

WHAT IS WRONG. `.aw/system/workflows/templates/agents-README.md` is emitted to `.aw/records/README.md`
on every fresh install (`engine.ensure_plans_readmes`, target `agents-README.md`). Its body tells the
reader that `.aw/records/` contains:

  - **`workflows/`** holds the installed agent-workflows framework ... See `workflows/index.md`

NEITHER PATH EXISTS. A fresh install into a scratch repo was verified: `.aw/records/workflows/` is
absent and `.aw/records/workflows/index.md` is absent. The framework actually installs to
`.aw/system/workflows/` (constant `AW_SYSTEM_WORKFLOWS_DIR`), and `_record_scaffold_dirs('aw')`
scaffolds no `workflows` key at all. So the closing line 'You own `plans/`; the framework owns
`workflows/`' names a directory the layout retired, and the reader's only cited next step
(`workflows/index.md`) is a dead link.

WHY IT SURVIVED. The template is pre-`.aw/`-layout prose that was correct when records and workflows
were siblings under `.agents/`. The four existing assertions over this file
(`tests/test_dir_readmes.py:47`, `:68`, `:72`, `tests/test_record_producers.py:364`) check EXISTENCE
and path suffix only, so nothing pins the content and the drift is invisible to the suite.

WHY IT IS FILED RATHER THAN FIXED. Order 04's finding F-6 established that this template is the
CORRECT one for the records tree (against the workflow-artifacts README that had been wrongly copied
over this repo's own `.aw/records/README.md`), and E-03 explicitly scoped the template OUT: 'the
shipped template is UNCHANGED; a modified template is a FAILED validation'. That ruling is about the
'DO NOT gitignore' defect and remains right. This is a SEPARATE, narrower factual error in the same
file, found while verifying F-6, and editing it would have failed Order 04's own V-03.

SUGGESTED FIX. Update the template to describe the trees the `aw` layout actually scaffolds (point at
`.aw/system/workflows/index.md` for the framework, and list the typed record trees), and add one
CONTENT assertion so the next layout change cannot silently invalidate it. This repo's own
`.aw/records/README.md", rewritten by Order 04 E-03, is a usable reference for the corrected shape.
