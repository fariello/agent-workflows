- Id: tl8qmc
- Status: done
- Graduated-To: tl8qmc
- Blocks-Release: next
- Set: tl8qmc
- Priority: medium
- Work-Kind: bug
- Summary: backlog.py stamps history with the LOCAL date while status_set.py stamps the UTC date, so between local midnight and UTC midnight the two setter spellings write different dates and their parity test fails

## Workflow history
- 2026-10-09 note (aw backlog): The test_release_exempt_setter_roundtrip_and_parity symptom no longer reproduces: commit da04c5cf0 masked the date in that test, and commit 3c55295a3 (plan 5ivkdh) removed that mask, so the test now compares dates literally and passes because the clock is fixed; see the driven reproduction across both aw backlog set spellings under a skewed timezone (Pacific/Honolulu) as the authoritative check. On tl8qmc: the item stays graduated to live carrier dmrbqa, which owns the residual local-clock record_history.append/append_rename sites deferred by 5ivkdh.
- 2026-10-07 done (aw backlog): closed by aw agy run: IPD dmrbqa executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-tl8qmc-01-dmrbqa-put-the-gitignored-history-sidecar-on-the-utc-clock-so-one-e.ipd.md); evidence .aw/records/plans/executed/20261002-tl8qmc-01-dmrbqa-put-the-gitignored-history-sidecar-on-the-utc-clock-so-one-e.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: dmrbqa
- 2026-09-30 created (aw backlog): Measured 2026-09-30 20:06 EDT / 2026-10-01 00:06 UTC while authoring plan fqcax0: tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity fails deterministically inside the local/UTC date gap.

MEASURED WHILE AUTHORING PLAN fqcax0. Unrelated to that plan, which touches no .py file; found because the authoring turn ran the suite inside the window where the two clocks disagree.

THE DEFECT. Two history-stamping paths disagree on which clock names 'today'. 'backlog.py' uses the LOCAL date ('datetime.date.today().isoformat()', five sites: the item renderer, the creating path, the filename date, the 'args.date' default, and one more). 'status_set.py' uses the UTC date ('datetime.datetime.now(datetime.timezone.utc).date().strftime("%Y-%m-%d")', one site, feeding the history entry, the Approval line, and the record_history call). So in any timezone behind UTC, between local midnight and UTC midnight, the same logical operation writes a DIFFERENT date depending on which spelling the operator used.

REPRODUCED DETERMINISTICALLY, not as a flake. At 2026-09-30 20:06 EDT (= 2026-10-01 00:06 UTC), 'python3 -m pytest tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity' fails on every run, with the diff naming exactly this: route 1 ('B.run_set') wrote '- 2026-09-30 HIST_ACTOR: exempted reason' and route 2 ('status_set.run_set_command') wrote '- 2026-10-01 HIST_ACTOR: exempted reason'. The test's whole purpose is to assert the two spellings produce byte-identical records after normalizing the id, summary and actor, so the date is the only field left disagreeing.

WHY IT IS A BUG AND NOT A TEST FLAW. The test is right: the two spellings ARE meant to be equivalent, and AGENTS.md treats the history line as a record a human and the attention view read. A record whose date depends on which of two equivalent CLI spellings was typed is wrong on its own terms, and worse, two items created minutes apart can be stamped a day apart, which misorders history and can move an artifact across any date-gated rule boundary.

USER-PERCEPTIBLE IMPACT, per the AGENTS.md gating test: for roughly the length of the UTC offset every day (4-5h in US Eastern, 7-8h on the US West coast), a maintainer running either setter gets a possibly-wrong date written into a durable committed record, and CI or a local suite run in that window fails on a test that has nothing to do with the change under test, which is exactly the 'inexplicable red' that costs a debugging round trip. That is what earns the 'bug' classification and the release gate rather than 'chore'.

THE FIX SHAPE. Pick ONE clock and route both modules through a single shared helper rather than repeating a 'today' expression in each; do not fix only the failing site, since 'backlog.py' alone has five. Which clock is the decision to record: UTC is reproducible across contributors and matches 'status_set.py'; the LOCAL date matches what a human believes the date is and matches the five 'backlog.py' sites plus 'record_history.py' (which also uses '_date.today()'). Note the filename-date site ('backlog.py' line stamping '%Y%m%d') is part of the same question, because a record's filename date and its first history date should not disagree either.
