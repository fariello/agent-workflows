- Id: fnb8pl
- Status: open
- Blocks-Release: next
- Set: fnb8pl
- Priority: medium
- Work-Kind: bug
- Summary: The two 'aw backlog set' spellings stamp history dates from different clocks (backlog.py uses local date.today(), status_set.py uses UTC), so in any timezone behind UTC one transition records two dates and test_release_exempt_setter_roundtrip_and_parity fails for part of every day

## Workflow history
- 2026-09-30 created (aw backlog): Found while validating plan t9lcdu (gzmr54-01); NOT caused by it. Reproduced at HEAD 2e2ecce12 in a clean detached worktree containing none of that lane's files: '1 failed' on the bare suite and on the narrowed run. The diff is purely the date, '- 2026-09-30 HIST_ACTOR: exempted reason' versus '- 2026-10-01 HIST_ACTOR: exempted reason', with labels and actors already normalized by the test. Cause: agent_workflows/backlog.py stamps history with datetime.date.today().isoformat() (five sites, local clock) while agent_workflows/status_set.py uses datetime.datetime.now(datetime.timezone.utc).date() (UTC). Machine local date was 2026-09-30 while UTC was 2026-10-01, so the two writers disagreed. This is time-dependent, not order-dependent: it is green for the part of the day when local and UTC dates coincide, which is why CI has not caught it. Distinct from the label defect that plan jbipfa (histlabel-01) owns on this same test; jbipfa rewrites the label normalization and would not fix the clock skew.
