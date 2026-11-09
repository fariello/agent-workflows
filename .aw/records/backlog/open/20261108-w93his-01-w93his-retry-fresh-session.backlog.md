- Id: w93his
- Status: open
- Blocks-Release: next
- Set: w93his
- Priority: high
- Work-Kind: bug
- Summary: Runner correction/retry turns resume the failed attempt's session, so they start with its full context (measured 324K tokens) and run slower and costlier; start them fresh with only the failed predicates

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-09 note (aw backlog): proofread per the technical writing standard (spec ecmw83 R-08); meaning unchanged
- 2026-11-08 created (aw backlog): Runner correction/retry turns resume the failed attempt's session, so they start with its full context (measured 324K tokens) and run slower and costlier; start them fresh with only the failed predicates

## Problem

When an execute turn fails in a retryable way (a stall timeout, an interrupted turn, a finalize refusal handed back for correction), the runner starts a correction turn. `runner_shared.try_adopt_fix_it_lane` re-adopts the failed attempt's lane and, whenever the lane is safe to adopt and a prior session id is recorded, sets `session_id = prior_session_id`, so the host RESUMES the failed attempt's conversation. The correction prompt already carries "only the predicates that failed", but the resumed session brings the entire prior conversation with it.

Measured in run `run-20261107T082247Z-2899457`, plan `2xwb9b`:

| Turn | Wall time | Model steps | Context at start | Context at end |
|---|---|---|---|---|
| attempt 1 | 292 min | 98 | 61K tokens | 287K tokens |
| attempt 2 (resumed attempt 1's session) | 117 min | 85 | 324K tokens | 436K tokens |

Attempt 2 started where attempt 1 ended, so every one of its model steps re-read about 324K to 436K tokens. That is user-perceptible: each correction turn costs more and replies more slowly than a fresh turn on the same work, and a turn already near its context limit has the least room to finish. Attempt 2's 17 steps in its first 44 minutes cost $7.60.

## Proposed fix

A correction or retry turn starts a FRESH host session by default, in the re-adopted lane (the lane's commits and files are the durable state, so nothing is lost), with a prompt that carries the failed predicates, the lane's `git log` since base, and a short summary of what the prior attempt recorded (its outcome file and any lane-submission report). Keep resuming the session as an explicit opt-in (`--resume-correction-session`), for the case where the prior conversation holds reasoning that is not in the lane.

Acceptance: a test drives a failing execute turn with a fake host and asserts the correction turn's launch carries no resume-session argument and its prompt carries the failed predicates; with the opt-in, it carries the prior session id. The measured case above is the regression record.

## Related

- The step-complexity split of the metastore Set (2026-11-07) attacks the other half of the same cost: single plan items that hid hundreds of steps and let one turn's context grow past 280K tokens.
