- Id: wkpcop
- Status: open
- Set: histdedup
- Priority: low
- Work-Kind: chore
- Summary: backlog._prior_history_records and attention._history_section_lines bound the history block by different rules, so a dedup predicate answer can disagree with the restorable prior records

## Workflow history
- 2026-10-02 created (aw backlog): Measured while authoring plan evbx9s from backlog r74211: the two readers disagree on whether an INDENTED history-shaped line is a record, which lets a suppressed write empty the history block with no validation finding.

Measured 2026-10-02 at HEAD `f55aed0b` while authoring plan `evbx9s` (from backlog `r74211`), with that plan's candidate fix applied as a throwaway probe.

THE OBSERVATION. Two readers partition a backlog item's `## Workflow history` by DIFFERENT rules:

- `backlog._prior_history_records` requires a record to start at COLUMN ZERO (`ln.startswith("- ")`). Its docstring justifies that with the measured `tk1gqo` incident, in which five INDENTED, prose-quoted example lines inside an item's body matched as records and were re-emitted into the history block, turning 11 records into 17 and promoting quoted examples into the item's own provenance.
- `attention._history_section_lines`, which `status_set.same_status_message_is_duplicate` reads through (via `attention_contract.newest_history_record`), applies NO such rule.

So on an item whose only history-shaped line is indented, the predicate reports a DUPLICATE while `_prior_history_records` reports NO prior records. Measured on exactly such a fixture: predicate -> True, `_prior_history_records` -> `[]`.

WHY IT MATTERS, AND WHY IT IS FILED RATHER THAN FIXED. Plan `evbx9s` wires the predicate into `backlog.run_set` so an idempotent same-status re-assertion stops appending a duplicate record. With the probe applied and no guard, that fixture was written back with `## Workflow history` followed by blank lines and NO record inside the block, and `backlog.validate_item` returned NO drift on the result, so nothing in the tree catches it. `evbx9s` E-04 therefore FAILS SAFE (it declines to suppress when the prior-record list is empty), which turns the one measured invisible-loss case into a harmless extra record but does NOT reconcile the two readers.

WHY THE RECONCILIATION IS ITS OWN REVIEW. Either direction has a real cost. Loosening `_prior_history_records` to match `_history_section_lines` would re-open the pinned `tk1gqo` data-loss fix. Tightening `_history_section_lines` to require column zero changes a reader with many consumers across the attention and readiness surfaces, including `plan_readiness` verdict reading, so its blast radius is far larger than the dedup change that exposed it.

SUGGESTED SHAPE. Decide which bounding rule is canonical for a history block, state it once (a shared bounded-section reader both sides call), and migrate the consumers to it, rather than leaving two partitioning rules that agree on every well-formed artifact and disagree exactly on the malformed ones. Note that nothing currently REFUSES an item whose history block is empty, so a validation rule for that is a cheap independent backstop.
