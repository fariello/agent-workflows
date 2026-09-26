- Id: sm0vgn
- Status: graduated
- Graduated-To: staledocs
- Blocks-Release: next
- Set: cutoverdoc
- Priority: medium
- Work-Kind: bug
- Summary: docs/cli-migration.md and docs/cli-agent-protocol.md still promise a non-TTY hard cutover to JSONL that was RETRACTED on 2026-09-10 and never happened

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set staledocs (commit 2c7068ca).
- 2026-09-24 created (aw backlog): docs/cli-migration.md and docs/cli-agent-protocol.md still promise a non-TTY hard cutover to JSONL that was RETRACTED on 2026-09-10 and never happened

Carrier re-pointed from plan 7p3tt8's deferred row 5, whose declared carrier yaxr4i is EXECUTED, so nothing was going to revisit it. check.ipd-uncarried-obligation caught that at 7p3tt8's finalize.

MEASURED 2026-09-24 in lane aw/lane/7p3tt8_attempt2:
  docs/cli-migration.md:1   '# CLI output migration guide (2.0.0 hard cutover)'
  docs/cli-migration.md:5   'This is a HARD CUTOVER with NO ...'
  docs/cli-agent-protocol.md:11  'This is a HARD CUTOVER as of the ...'

THE PROMISE IS FALSE, verified rather than assumed: 'aw status | cat' emits human prose ('agent-workflows status', 'Environment:'), not aw.agent/v1 JSONL. The maintainer RETRACTED the automatic non-TTY cutover on 2026-09-10 (yaxr4i OQ-01, Option B). Plan 7p3tt8 corrected the same claim in docs/cli-human-guide.md (its E-02 conditional half) and could not reach these two files: they are outside its Scope-Paths fence.

THE FIX IS THE SAME SHAPE 7p3tt8 USED: label the policy RETRACTED with a pointer to the 2026-09-10 ruling; do NOT delete it silently, which would erase the record that it was ever promised. docs/cli-migration.md needs more than a line edit, since its TITLE and its 'Why a hard cutover' section are both built on the retracted premise.
