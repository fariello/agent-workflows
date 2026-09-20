- Id: fwq5nu
- Status: open
- Blocks-Release: next
- Set: bklgdupe
- Priority: high
- Work-Kind: bug
- Summary: Eight backlog items are tracked in BOTH graduated/ and done/ with the same id6, so one item exists as two files and aw find/attention see a duplicate identity

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing IPD sk7ggr E-05, whose terminal-inclusive id6 collision scan made these visible on 'aw check all' for the first time (1 -> 10 findings; 8 of the 9 new ones are this defect). THE EIGHT: yw6759 (corpuspin), s9p5x5 (grouporder), gjadwm (gatejrnl), plbkp5 (awinbox), bplplj, fjs11i (hardreach), f8m2z2 (findtwotier), rxya25. Each has a byte-DIFFERENT copy tracked in git HEAD under BOTH .aw/records/backlog/graduated/ and .aw/records/backlog/done/, with the graduated copy carrying '- Status: graduated' and the done copy '- Status: done'. Verified with 'git ls-tree -r HEAD' (both paths present for all eight) and md5sum (contents differ). INDEPENDENTLY CORROBORATED: 'aw attention --format json' already reports valid:false with eight attention.duplicate-id violations naming exactly these pairs, so the defect is real and pre-existing rather than an artifact of sk7ggr's change. LIKELY MECHANISM, stated as a hypothesis for whoever fixes it rather than as a finding: a status transition that WROTE the new-status file without REMOVING the old-disposition one; 'git log' shows the graduated copies landing in a graduation commit (399d8d9d) and the done copies in later 'closed by aw oc run' commits, so the closing path appears not to have deleted its predecessor. WHY IT MATTERS: every aw verb resolves an artifact BY id6, so a command silently operates on whichever of the two files it found first, and the item's true status is ambiguous. NOT FIXED HERE: sk7ggr's execution contract forbids editing or renaming records, and deciding which copy is authoritative per item is a maintainer call.
