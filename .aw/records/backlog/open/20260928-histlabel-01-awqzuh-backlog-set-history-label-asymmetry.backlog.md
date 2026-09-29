- Id: awqzuh
- Status: open
- Set: histlabel
- Priority: low
- Work-Kind: chore
- Summary: aw backlog set writes a different history label depending on spelling: done (aw set) positionally versus set (aw backlog) with --status

## Workflow history
- 2026-09-28 created (aw backlog): aw backlog set writes a different history label depending on spelling: done (aw set) positionally versus set (aw backlog) with --status

Measured at plan review of eikajx (2026-09-28) by driving both spellings over identical fixtures in scratch repositories.

THE OBSERVATION. The two spellings of the same transition write DIFFERENT history labels:

  aw backlog set done <id6>              ->  - <today> done (aw set): <message>
  aw backlog set <id6> --status done     ->  - <today> set (aw backlog): <message>

The positional spelling routes through `status_set.apply_status_change`, which builds its record as `f"- {today} {status_tag} ({actor}): {message}"`, so the label is the TARGET STATUS. The `--status` spelling routes through `backlog.run_set` -> `backlog._reattach_history`, which HARDCODES `new_record = f"- {today} set (aw backlog): {msg}"` and uses its `new_status` parameter only as a message fallback (`msg = message.strip() or f"status -> {new_status}"`).

BOTH PRESERVE PRIOR RECORDS CORRECTLY, so no provenance is at risk. This is a cosmetic and queryability inconsistency, not a data-loss defect, which is why it is filed `chore`.

WHY IT IS WORTH TRACKING. The repository's own corpus shows the status-label convention is the dominant one: measured across .aw/records/backlog/*/*.backlog.md, the labels are `created` 622, `set` 318, `graduated` 262, `done` 187, `open` 90, `note` 25. So 318 records carry the uninformative `set` label where the writer knew the target status and could have recorded it. A reader scanning history cannot tell from a `set` record what the transition was without reading the message.

NO MACHINE CONSUMER IS AFFECTED TODAY, which bounds the urgency. `attention_contract.HISTORY_RECORD_RE` is `^- (?P<date>\\d{4}-\\d{2}-\\d{2}) .+$`, so only the DATE is grammatical. The one place a label IS consumed, `ipd_lifecycle._plan_status_events`, gates on `_PLAN_STATUS_VOCAB` and applies to PLANS, not backlog items.

SUGGESTED FIX, with its risk stated. Give `backlog._reattach_history` the label as a parameter (defaulting to today's behavior so no caller changes silently), and pass the target status from `run_set`. THE RISK IS THE REASON THIS IS NOT A ONE-LINER: `_reattach_history` is the shared preserving writer that plan vhbvwz E-08 built, every `--status` transition goes through it, and it is deliberately fenced OUT of scope by plan eikajx. So whoever takes this should own the shared-writer change deliberately, with tests over both spellings.

DO NOT 'FIX' THIS BY MAKING close_on_answer PATCH THE LABEL AFTER THE CALL. That re-creates the bespoke per-caller history writer that eikajx exists to delete.

NOTED AT: plan eikajx review, finding F-13 / decision D-3. eikajx deliberately ACCEPTS the `set (aw backlog)` label rather than widening the shared writer.
