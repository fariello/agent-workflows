# .agents/backlog/

The attention-visible BACKLOG TIER (spec `20260813-1833-01`). A lightweight, tracked place for
COMMITTED and candidate work, so `aw attention` (which feeds `/whatnext`) is not silently blind to
work that used to live only in the free-prose `TODO.md`.

This is a `records`-class sub-tree: it materializes here at `.agents/backlog/` pre-migration and at
`.aw/records/backlog/` after the awphysical layout migration (dual-path, like `plans`).

## Layout (status by directory)

```
backlog/
  open/      committed, actionable now        -> aw attention class: ready
  blocked/   committed but gated              -> blocked  (requires a typed Gate-Kind/Gate-Ref)
  parked/    uncommitted "maybes"             -> parked   (hidden from the default board; --all to show)
  done/      completed/closed                 -> done
```

Committed (`open`/`blocked`) items show in `aw attention`; uncommitted `parked` maybes are tracked
but hidden until `aw attention --all`. This is the three-tier model: committed work needs attention;
maybes stay quiet; pure context/notes are NOT backlog items (they stay in `TODO.md`'s Notes).

## Item format

One item per file, `- Field:` bullet metadata (same grammar as specs/plans; the gate reuses the
attention `Gate-Kind`/`Gate-Ref` bullets), then a prose body:

```markdown
- Id: <id6>
- Status: open | blocked | parked | done
- Set: <terse-id>
- Priority: high | medium | low
- Kind: bug | feature | chore | security | followup
- Summary: <one line>
- Gate-Kind: <artifact|decision|todo|issue|date|external>   # iff blocked
- Gate-Ref: <ref>                                            # iff blocked

## Workflow history
- YYYY-MM-DD <event> (<actor>): <one line>

<free prose body>
```

Status is encoded BOTH by directory and by the `- Status:` bullet, and the two MUST agree.

## Verbs

- `aw backlog new --summary ... [--status --priority --kind --set --slug --gate-kind --gate-ref --body] [--apply]`
  create a conformant item (dry-run by default; owns the clustering filename + metadata).
- `aw backlog set <path> --status <open|blocked|parked|done> [--message ... --gate-kind ... --gate-ref ...]`
  transition status (moves the file between the disposition dirs), append a history record; moving to
  `blocked` requires a typed gate.
- `aw backlog check [--agent]` validate the tree fail-closed (valid enums, status-mirrors-directory,
  gate present-and-valid iff blocked, unique id6, nonempty summary).

## Promotion to a plan

When a backlog item becomes committed execution work, author an IPD under `.agents/plans/pending/`,
then `aw backlog set <item> --status done` with a history line citing the plan id. The backlog captured
the intent; the plan owns execution.

Do NOT hand-name backlog files or hand-edit status inconsistently with the directory; use the verbs.
