- Id: byazcp
- Status: graduated
- Graduated-To: byazcp
- Blocks-Release: next
- Set: byazcp
- Priority: medium
- Work-Kind: bug
- Summary: oc run silently resolves a contradictory verification flag pair by argparse last-wins, where agy refuses it

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: zdgc6t
- 2026-09-28 created (aw backlog): Filed while authoring plan 7dz3wv (graduating xdgorn); measured at HEAD beb37773.

Measured live at HEAD `beb37773` while authoring plan `7dz3wv`.

WHAT IS WRONG. On opencode, all six verification spellings (`--validate`, `--no-validate`, `--verify`, `--no-verify`, `--audit`, `--no-audit`) are aliases of ONE `argparse.BooleanOptionalAction` on dest `validate`. So a contradictory pair parses silently and is ORDER-DEPENDENT:

  aw oc run --no-verify --validate <sel>   ->  validate=True   (verify)
  aw oc run --validate --no-verify <sel>   ->  validate=False  (do not verify)

Antigravity REFUSES the same pair before the run starts. `agy_runipd.verification_flag_tristate` raises `runner_shared.RunFlagRefusal` ("--no-verify (or --no-audit) and --validate contradict each other"), and its docstring states the reasoning: "Letting either spelling silently win would make a verification decision the operator did not make, and BOTH directions of that error are bad: one skips a check that was asked for, the other pays for a check that was declined."

WHY IT IS A BUG AND NOT A CHORE. That reasoning applies verbatim to opencode and is implemented on neither of its subcommands. The user-perceptible impact is a verification decision the operator did not make, in a command whose whole purpose is deciding whether work gets independently verified: a run can silently skip the verifier turn the operator asked for, or pay for one they declined. It is silent in both directions, so nothing tells the operator which way it went.

WHY IT WAS NOT FIXED IN 7dz3wv. That plan is a documentation-and-pinning change that declares this behavior in spec 25kzda 2.1c and touches no source file. Fixing this is a behavior change on a shipped CLI and needs its own measurement of what invocations rely on last-wins.

SUGGESTED FIX: give oc the same pre-run refusal agy has, ideally by lifting `verification_flag_tristate`'s contradiction check into `runner_shared` so one predicate serves both hosts. NOTE THE OBSTACLE: on oc the six spellings share one dest, so a parsed namespace cannot distinguish `--no-verify` from `--no-validate` after the fact; detecting the contradiction needs either a custom action recording which spellings were seen, or an argv-level check. Plan `7dz3wv` E-02 pins the current order-dependent behavior in `tests/test_runner_shared.py`, so this fix has a baseline to change.
