- Id: fcnz1r
- Status: graduated
- Graduated-To: setdisp
- Set: fcnz1r
- Priority: medium
- Work-Kind: chore
- Summary: Unify the two aw backlog set dispatch paths so a behavior wired into one spelling cannot be missing from the other

## Workflow history
- 2026-10-01 graduated (aw backlog): graduated: 63zo2f, afdmn6, c6f6sj, m1jlwm, m94eht, vhiqo6
- 2026-09-29 created (aw backlog): Unify the two aw backlog set dispatch paths so a behavior wired into one spelling cannot be missing from the other

Filed while authoring plan 47ttnv (backlog mawwlc), which named this as its under-scope and needs a durable carrier for it.

ROOT CAUSE OF A RECURRING CLASS. 'aw backlog set' forks in cli.main on whether --status was PASSED: absent routes to status_set.run_set_command (the positional spelling), present routes to backlog.run_set. The two implement overlapping behavior separately, and the SAME class of defect has now been found on that fork THREE times:
1. 43p53n, gate-field clearing: status_set's own comment records 'backlog.run_set already cleared correctly, but the positional form routes here instead, so that fix was unreachable'.
2. nobugship/gatefollows, the release-gate default: fixed by deliberately wiring decide_gate_default into BOTH paths, whose comment states the principle: 'A default wired into one only would fire for one spelling of one verb and not the other, which is worse than not shipping it because it teaches a false expectation.'
3. mawwlc/47ttnv, the release-gate close predicate: the positional spelling closed a release-blocking item at exit 0.

Each was fixed by DUPLICATING the behavior into the second path, which is the correct minimal fix for a release-blocking bug and also why the class keeps recurring. The durable fix is one implementation.

KNOWN CONSTRAINTS, so this is not mistaken for a small refactor: run_set_command is reached by five CLI surfaces (aw set, aw ipd set, aw prompts set, aw specs set bare, aw backlog set positional) plus work_cmd's 'aw finish' delegation, and is shared by plans, specs, prompts and research; the two paths differ in ways that are each deliberate and separately pinned (git_mv single staged rename vs atomic_write+unlink, history sidecar written by one and not the other, --gate-dir honored by one only, multi-selector batch semantics on one only). So this needs a spec-level decision about which behaviors are canonical before any code moves.

Note 'aw specs set' carries the identical --status fork, so the same audit applies there.
