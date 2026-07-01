# Contributing

This repo's value is disciplined, honest documentation, so the one rule that matters
most is: keep the docs in sync with what the framework actually does.

## Doc-sync checklist: when you add or rename a workflow

The authoritative rules for how workflows are structured live in `ARCHITECTURE.md`
(see its "Capability layout" section) and `.agents/workflows/index.md` (the manifest
format). Do not restate those here; follow them, and use this as the step list:

1. Add or rename the workflow subdirectory under `.agents/workflows/<capability>/`.
2. Update the manifest row(s) in `.agents/workflows/index.md` (keep the
   `command | body | lens | description` columns stable).
3. For an `assess-*` concern, add the lens file under
   `.agents/workflows/assess/lenses/` and reference it in the manifest `lens` column.
4. Regenerate the per-tool slash-command shims by running the installer
   (`.agents/workflows/install-workflows.py`); do not hand-edit the generated shims in
   `.opencode/commands/` or `.claude/commands/`.
5. Confirm `README.md` and `ARCHITECTURE.md` still describe the current set accurately.
6. If a decision changed the design, add a dated entry to `DECISIONS.md`. Never rewrite
   existing dated entries to match a later layout; the log is history (see
   `GUIDING_PRINCIPLES.md` P4).

## Authoring conventions

- Match what the software does today; do not document aspirations
  (`GUIDING_PRINCIPLES.md` P2).
- Keep each policy or rule in exactly one canonical place and link to it, rather than
  duplicating it (P8).
- Do not use em dashes in authored Markdown; use hyphens or parenthetical dashes.
