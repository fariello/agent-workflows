- Id: mpghjn
- Status: open
- Blocks-Release: next
- Set: doctorhint
- Priority: medium
- Work-Kind: bug
- Summary: aw doctor's status-untooled remediation can never clear its own finding: a re-applied status writes a same-status history token that check_engine._has_matching_history_line rejects

## Workflow history
- 2026-09-25 created (aw backlog): aw doctor's status-untooled remediation can never clear its own finding: a re-applied status writes a same-status history token that check_engine._has_matching_history_line rejects

## Origin

Found during `/plan-review` of plan `6k7xot` (finding PR-004, decision D-1), which is the carrier
relationship in the other direction: that plan makes `aw doctor` stop CLAIMING the command, and this
item is the underlying defect that makes the command unable to work. `6k7xot` deliberately does not
fix this, because both candidate fix sites are outside its declared `Scope-Paths`.

## The defect

Two shipped components disagree about which history token a re-applied status writes:

- `status_set.apply_status_change` tags a write whose old status already equals the target as
  `same-status` (`status_tag = "same-status"`; its own docstring states this).
- `check_engine._has_matching_history_line` accepts only a line whose status token EQUALS the new
  status value.

A hand-edited `- Status:` is by definition ALREADY at the target value, so the remediation
`check.status-untooled` recommends can only ever produce the one token the checker rejects. The
finding is therefore unclearable by the command the tool prints.

## Reproduction (measured 2026-09-25 against this worktree)

Scratch repo, one plan carrying `Work-Kind`/`Priority` (needed to pass the approval floor), status
hand-edited from `to-review` to `approved` and staged:

```text
DRIFT BEFORE:                         [('check.status-untooled', '...demo.ipd.md')]
EMITTED COMMAND:                      aw set approved <id6>
FIX EXIT (with the id6 filled in):    0
history written:                      - 2026-09-25 same-status (aw set): status unchanged (approved)
DRIFT AFTER RUNNING THE PRINTED FIX:  [('check.status-untooled', '...demo.ipd.md')]
```

Exit 0, a success line, and the finding still present. Confirmed directly against the predicate:
`_has_matching_history_line(<same-status text>, "approved")` is `False`, while the same text with a
genuine `- 2026-09-25 approved (aw set): ...` line is `True`.

## Candidate fixes (decide; do not assume)

1. **Teach the checker the `same-status` tag.** Accept a `same-status` record as attribution when the
   staged status equals it. Smallest change; the risk is that it weakens the very signal the rule
   exists to detect (a hand edit followed by a no-op `aw set` would then pass).
2. **Have the setter write a genuine transition record when the on-disk status is untooled.** More
   faithful, but it needs a way to know the previous value, which is a git read the setter does not do.
3. **Change the recommended recovery, not the code.** Document the two-step revert-then-set path as
   the only correct recovery. Cheapest, and it leaves the one-command fix impossible.

RECOMMENDATION: (1) or (3). Do not pick (1) without checking whether it defeats the rule's purpose;
`check_status_untooled`'s docstring already records an accepted efficacy ceiling, and this decision
sits exactly on it.

## Related

- `x6tk1u` (done) and `hg2oop` (open) also concern same-status `set` behavior. Note `hg2oop`'s own
  "CORRECTED 2026-09-10" section: its history-truncation diagnosis was retracted by its author, so do
  not carry that claim into this fix.
- Separately observed while reproducing this, and NOT part of this item: `aw backlog set --dry-run`
  appears to write the file rather than preview it. That needs its own measurement and item.
