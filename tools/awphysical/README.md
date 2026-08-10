# AW physical-layout planning tools

These stdlib-only tools accompany the `awphysical` IPD Set. They provide an executable
starting point for the read-only evidence surfaces required by Orders 06 and 10. They are
not the production migration implementation and must not be treated as authorization to
move or delete files.

## Tools

- `aw_layout_inventory.py`: inventories declared legacy roots without following symlinks.
  It records file type, size, mode, SHA-256, and Git tracked/untracked/ignored state.
- `aw_layout_compare.py`: compares a frozen inventory and approved migration map with the
  actual source and destination files. It fails on missing, changed, duplicate, unknown,
  or unapproved items.
- `aw_layout_postcheck.py`: checks a resolved-context evidence file for physical-root,
  tracking, runtime-ignore, authority, retained-source, and producer-routing violations.
- `migration-followup-review.md`: a self-contained instruction for a fresh agent to review
  deterministic migration evidence and identify remaining work.
- `migration-scenarios.json`: the closed initial scenario catalog that Order 12 must bind to
  executable tests and documentation.
- `test_awphysical_tools.py`: isolated tests for the three Python tools.

## Safety boundary

The tools read files and Git metadata. They write only an explicitly requested JSON output
file. They do not copy, move, delete, stage, commit, push, modify remotes, or change AW
policy. Run them from a disposable fixture before using them on a real project.

## Example

```bash
python3 tools/awphysical/aw_layout_inventory.py \
  --repo . \
  --output /tmp/aw-inventory.json

python3 tools/awphysical/aw_layout_compare.py \
  --inventory /tmp/aw-inventory.json \
  --map /tmp/approved-migration-map.json \
  --source repo=. \
  --destination records=/path/to/private-companion/.aw/records \
  --output /tmp/aw-compare.json

python3 tools/awphysical/aw_layout_postcheck.py \
  --context /tmp/aw-context.json \
  --output /tmp/aw-postcheck.json
```

The inventory omits absolute root paths by default. Add `--include-root-paths` only when
the evidence file will remain in an appropriately private location.

After extracting the overlay at the agent-workflows repository root, regenerate the plan
manifest with:

```bash
python3 -m agent_workflows plans index
```

Then run `/plan-review` on the orchestrator and each child before approval or execution.
Do not execute the Set merely because the structural author lint passed.

## Expected migration-map shape

```json
{
  "schema_version": 1,
  "inventory_id": "sha256 from the inventory",
  "items": [
    {
      "item_id": "inventory item id",
      "disposition": "copy",
      "destination_root": "records",
      "destination_relpath": "plans/pending/example.md"
    }
  ]
}
```

Allowed dispositions are `copy`, `deduplicate`, `retain`, and `exclude`. `exclude` requires
both `approved: true` and a nonempty `reason`. Every inventory item must appear exactly once.

## Postcheck context shape

The planning postcheck expects a future context evidence document with a `roots` object.
Each root-class entry contains `path`, `git_policy`, and optionally `git_root`. Required
classes are `system`, `config_project`, `config_local`, `state_durable`, `state_runtime`,
and `records`. The production schema is owned by Orders 01 and 02 and may replace this
planning shape while preserving these assertions.
