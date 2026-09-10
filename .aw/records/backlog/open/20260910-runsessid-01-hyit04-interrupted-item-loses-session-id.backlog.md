- Id: hyit04
- Status: open
- Set: runsessid
- Priority: medium
- Work-Kind: bug
- Summary: run state.json records session_id null for an interrupted item although its session log carries a real session id, so the Set is missing from run-summary session continuity and cannot be resumed under its session

## Workflow history
- 2026-09-10 created (aw backlog): run state.json records session_id null for an interrupted item although its session log carries a real session id, so the Set is missing from run-summary session continuity and cannot be resumed under its session

MEASURED 2026-09-10 in `run-20260910T004521Z-2724478` (opencode, 39 items, position 34, plan `utwr6y`),
which is the run that surfaced this. The item was killed by the stall guard after going silent
mid-review; that interrupt is correct and is NOT the defect. The defect is the bookkeeping around it.

THE SYMPTOM. The run's `state.json` records BOTH the item and its single attempt with
`"session_id": null`, while that attempt's own session log
(`sessions/34-utwr6y-attempt-1.jsonl`) carries a real one on every event (a
`ses_<opaque>` handle, redacted here because a session id is machine-local). So the id existed and was
reachable; it simply was never written back to the run state.

THREE CONSEQUENCES, in increasing order of cost. FIRST, the run summary's "OpenCode Session Continuity"
block lists 31 Sets and `testiso` is absent, because that block is keyed on the recorded id. SECOND,
the operator-facing remedy the summary prints (`aw oc run --session <id> <selector>`) is therefore
unavailable for exactly the item that needed it most: the one that did not finish. THIRD, and this is
what makes it worth fixing rather than noting, the lost id is the pointer to 15 recorded reasoning steps
that a resume could otherwise build on. In this instance that work WAS recoverable, but only because a
human went looking in the log by hand.

NOT A DEAD SESSION, so do not diagnose it as one: that same session id is shared by four
other Sets in the same run (`auditshare`, `defreport`, `hardreach`, `specfresh`), ALL of which completed
and ARE listed under session continuity. The session was alive and productive; only this attempt's
record of it is empty.

WHERE TO LOOK, offered as a starting point and not a diagnosis: whichever writer persists
`attempts[].session_id` presumably runs on the normal completion path, so an interrupt that unwinds
earlier would skip it. The fix is likely to capture the id when the session STARTS (it is present on the
first event) rather than when the turn ends, so an abnormal exit cannot lose it. Verify that claim
against the code before acting on it; it is an inference from the artifact, not a reading of the writer.

ADJACENT, worth checking in the same pass: whether any OTHER per-attempt field is written only on the
success path and therefore silently empty for every interrupted item.
