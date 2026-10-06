- Id: eeiytw
- Status: open
- Graduated-To: eeiytw
- Blocks-Release: next
- Set: eeiytw
- Priority: low
- Work-Kind: bug
- Summary: aw rename plans and aw group plans emit no aw.agent/v1 payload at all under --json/--agent, and print a nested index-refresh line onto stdout

## Workflow history
- 2026-10-06 open (aw set): z2l43n returned to authoring: uncovered obligation: Close backlog item eeiytw by making both verbs emit exactly one parseable aw.agent/v1 record; re-run graduation to complete the handoff
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: gzb2rq, vfqjc0, x7unul, z2l43n
- 2026-09-30 created (aw backlog): Filed by /plan-review of plan wgp0g3 2026-09-30 to carry that plan's F-12 deferral.

MEASURED 2026-09-29 while authoring plan `wgp0g3` (recorded there as F-12) and re-derived at its review 2026-09-30.

`aw rename plans <id6> --slug ... --apply --json` exits 0 and writes to stdout:

    renamed <old> -> <new>
    wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)

`json.loads(stdout)` raises. `aw group plans ... --json` has the same shape, and so does `--agent` for both.

WHY THIS IS A DIFFERENT DEFECT FROM `wgp0g3`'s, and why that plan deliberately did not fix it: there, a WORKING `aw.agent/v1` payload was being POLLUTED by a nested line, so silencing the line fixes it. Here there is no payload at all: measured, `'aw.agent/v1' in stdout` is False and stdout contains no `{` whatsoever. Silencing the nested line would leave stdout EMPTY rather than parseable. So this is UNIMPLEMENTED machine support for two mutation verbs, not pollution of a working one, and the fix touches `plans_refs.py`, `artifact_rename.py` and the renderer wiring.

THE CONTRACT THIS VIOLATES is already written: `docs/cli-output-contract.md` Section 7 reserves stdout for structured results and Section 11.2 forbids progress cues there; spec `command-surface-redesign` R4/AC5 require every cross-cutting verb to honour `--json`/`--agent`.

WORK-KIND bug AND RELEASE-GATING, on the same reasoning `wgp0g3` carries: a documented machine surface that a programmatic consumer cannot parse is a user-perceptible defect, not a chore. A consumer of these two verbs cannot script them at all today.

SCOPE NOTE: the nested `run_index` regeneration line here comes from a call that passes NO `quiet` key, unlike the three other nested callers (`status_set._auto_index_types` and two in `artifact_rename`) which pass `quiet=True` and are therefore silent. So part of the fix is trivially available; the payload half is the real work.
