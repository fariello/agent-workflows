- Id: mod4ml
- Status: open
- Set: mod4ml
- Priority: low
- Work-Kind: chore
- Summary: aw specs set has no --from-backlog flag, so a spec-first graduation has no setter route to record or inherit its gate

## Workflow history
- 2026-09-18 created (aw backlog): aw specs set has no --from-backlog flag, so a spec-first graduation has no setter route to record or inherit its gate

Found while executing plan `di08i9` (Set `nobugship`) building that plan's V-03 route inventory. The
plan names this gap in its own "Deferred / out of scope" section, so it is a KNOWN asymmetry rather
than a discovery; this item exists so the gap has a durable carrier instead of living only inside a
plan that is about to become terminal.

THE ASYMMETRY. A spec is an ACCEPTED release-gate carrier: `check_engine.find_from_backlog_artifacts`
scans specs as well as plans, `evaluate_blocking_close`'s HANDOFF branch accepts a spec, and
`AGENTS.md` names both ("A SPEC may carry the same field and is an equally valid gate carrier"). But
`--from-backlog` is registered on exactly ONE parser, `p_ipd_set` (`cli.py:1307-1312`). Driven:

```text
$ python3 -m agent_workflows specs set --help
  ... --blocks-release BLOCKS_RELEASE ... --priority ... --work-kind ... --evidence ...
  (no --from-backlog)
```

So `aw specs set --blocks-release` can set a spec's gate, but nothing can record the LINK that makes
it a provable handoff, and a spec-first graduation can only acquire `- From-Backlog:` by hand editing.

CONSEQUENCE. Plan `di08i9` E-03 made `aw ipd set --from-backlog` inherit the item's gate
automatically; a spec cannot benefit, because the flag it would hang off does not exist. The
close-legitimacy predicate still ACCEPTS a hand-authored spec carrier, so nothing is broken today:
this is a missing convenience and a consistency gap, which is why it is filed `chore` rather than
`bug`.

SUGGESTED FIX. Add `--from-backlog` to the `aw specs set` parser. The write side needs no new code:
both verbs route through `status_set.apply_status_change`, whose `From-Backlog` write and the new gate
inheritance beside it are already record-type-agnostic, so registering the flag should be sufficient.
Worth confirming against `command_surface.py`'s declared flag set for that command in the same change.
