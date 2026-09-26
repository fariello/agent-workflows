- Id: zi2uzu
- Status: graduated
- Graduated-To: carrierwarn
- Set: zi2uzu
- Priority: medium
- Work-Kind: chore
- Summary: A pending plan's Deferred carrier can go terminal under it with nothing noticing until the next commit, so the plan's obligations silently lose their carrier

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set carrierwarn (commit 2c7068ca).
- 2026-09-23 created (aw backlog): Found while executing 40it5e (rununify 12), where it cost a refused commit mid-turn. 40it5e's Deferred rows named carrier gqo6if, which was pending when 40it5e was reviewed on 2026-09-22 and reached executed on 2026-09-23. NOTHING FLAGGED THE TRANSITION. The refusal arrived only when 40it5e's executor ran 'aw commit' the next day and check.ipd-uncarried-obligation reported '2 obligation(s) name no durable carrier: carrier gqo6if resolves only to a terminal/hidden artifact (executed); nothing revisits it'. THE GATE IS CORRECT and this is NOT a request to weaken it: a deferral pointing at an executed plan genuinely names nothing that will revisit it, and the terminal-carrier skip in check_engine (narrowed by the qmgn12 OQ-03 ruling) is right too. The gap is TIMING and DIRECTION: the obligation is checked when the DEFERRING plan is touched, but the event that invalidates it is a transition of a DIFFERENT artifact, so the window between the carrier going terminal and the deferring plan next being committed is unbounded, and in that window aw check reports a clean tree while a live plan's obligations have no carrier. Every plan that deferred to gqo6if is affected, not just this one. Possible shapes, not decided here: have the finalize transaction report which live artifacts name the finalizing plan as a Carrier (it already knows the id6 and already reconciles scope, so this is one reverse lookup), or surface the condition in aw attention so it is visible without touching the deferring plan, or both. The honest cost today is that an executor discovers it as a commit refusal partway through an unattended turn and must re-point another plan's deferral rows as unplanned work.
