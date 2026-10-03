- Id: 8ctu3u
- Status: open
- Set: 4xtpvg
- Priority: low
- Work-Kind: followup
- Summary: A non-isolated unattended opencode turn gets no permission deny posture, so it relies on --auto plus the stall watchdog; 24 of 45 measured non-isolated driver asks postdate the isolated-turn posture

## Workflow history
- 2026-10-01 created (aw backlog): Filed while authoring plan 0b7fic (from backlog 4xtpvg) as that plan's declared carrier for its finding F-8. THIS IS A DELIBERATE NARROWING, NOT A DEFECT, and the item exists to get a maintainer decision rather than to report a bug. MEASURED at HEAD ce55ef615, numbers in research 7so8uz. oc_runipd.run_opencode applies lane_containment.build_permission_policy_env inside `if work_dir:`, so permission.external_directory=deny and permission.question=deny reach the host ONLY for an ISOLATED turn. The in-code rationale is explicit: "ISOLATED TURNS ONLY, deliberately narrower than the bounds below. R4.1 scopes the posture to an unattended ISOLATED turn, and a non-isolated turn legitimately works in the main checkout, where an external-directory denial would refuse its ordinary work." Spec 7ckptx R4.1 says the same, so code and spec agree.

CONSEQUENCE, MEASURED: a non-isolated unattended turn can still be ASKED a permission it has no answerer for. Over the host log's 1,166 driver-attributable permission asks, 45 are on non-isolated turns and 24 of those 45 POSTDATE commit 8a491d4c1 (2026-09-05), the change that landed the deny posture, precisely because that posture does not apply to them. Isolated-turn asks fall 1,102 -> 19 -> 0 across the same boundary while non-isolated asks do not.

WHY IT IS STILL BOUNDED RATHER THAN FATAL: `--auto` auto-approves anything not explicitly denied, and the StallWatchdog (DEFAULT_STALL_TIMEOUT = 900.0, advanced by stdout and by stall_progress's subagent log observer) terminates a silent child. Research 7so8uz measured that all 17 asks in the corpus that were followed by no further stdout at all also had no subagent progress, so the watchdog covers them. So this is RESIDUAL EXPOSURE, not a live hang: no non-isolated deadlock has been observed.

WHAT THE DECISION IS, and why it is not obvious: narrowing a non-isolated turn's permissions could REFUSE THAT TURN'S ORDINARY WORK, which is the opposite failure and a worse one, since a non-isolated turn's whole job is in the main checkout. So the options are (a) leave it, documented, which is today's state; (b) deny only `question` and not `external_directory` for a non-isolated turn, on the reasoning that an unanswerable interactive question is never legitimate while an out-of-checkout path sometimes is; (c) deny nothing and rely on the bounds, documenting that the host layer contributes nothing for this turn class, which is already antigravity's permanent posture per R4.1c. Option (b) looks most promising and is UNMEASURED: nobody has checked whether a non-isolated turn ever legitimately needs `question`.

NOT A RELEASE BLOCKER: Work-Kind is followup, not bug. Nothing is user-perceptibly broken, no deadlock has been observed on this path, and the behavior matches the approved spec. If a real non-isolated deadlock is ever observed, that observation is a bug and should be filed as one with this item as context.
