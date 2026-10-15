# Review findings: plan aka0li

- Subject-Id: aka0li
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author` was clean before the review, and `--phase review-finalize` is clean after it. Pre-transition lint shows only the expected `IPD-S404` not-yet-performed items, so the carrier rules hold.

I prototyped all four planned behaviors in a scratch test under the gitignored `tmp/`, deleted afterwards. It used `tests.support.init_repo`, the `_CONFORMING_PLAN` fixture, a patched `run_queue`, and a real `fcntl.flock`, and it passed on both hosts:

- stop unknown -> `rc 2` with `Run not found: run-nonexistent-abcdef (nothing was created or modified)`
- stop live -> `rc 0`, `stop accepted: level 3 (now)`, the host hint, `read_stop_request(...).level == 3`, and one run dir
- oc audit -> `rc 1`, refused `audit-plan-not-executed` / `audit-plan-not-found`
- agy audit -> `rc 2`, "not implemented on the Antigravity host" / `aw oc run audit <id6>`

Mutation probe: I removed each verb from each host's `subcommands` and restored the file in `finally`, with sha256 equal and `git diff --quiet -- agent_workflows/` exit 0. Every one of the four pairs turned the scratch suite red:

- `stop` failed only the live-stop method: argparse `unrecognized arguments: --now`, `2 != 0`.
- `audit` failed only the matching-Set method: on both hosts a run dir `run-<ts>-<pid>` was minted and the patched `run_queue` raised.
- Under each mutation, the unknown-run stop and the unknown-plan audit both still returned `rc 2` with no run dir. Those methods discriminate only through their stderr assertions.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Mutation sensitivity / test intent | Probe: with `"stop"` removed, `stop run-nonexistent-abcdef --now` exits 2 via argparse (`unrecognized arguments: --now`) with no run dir; with `"audit"` removed, `audit nosuch` exits 2 with `No IPD plan found with id6 'nosuch'` and no run dir | Two of the four methods produce the same exit code and the same no-run-dir outcome under the mutation they are meant to catch. Only their stderr text tells the routes apart. The plan presented all four as rewrite guards and did not mark the stderr assertions as load-bearing, so an executor could weaken them and leave a method that cannot fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and E-03 now label those methods as routing characterizations, make the stderr assertions mandatory, and name the live-stop and matching-Set audit methods as the mutation-sensitive ones. |
| PR-002 | LOW | IN-SCOPE | E. Verification specificity | E-04 / V-04 said only "the corresponding test failing" | The demanded evidence did not say which node should fail or why, so a red caused by something unrelated (an import error or fixture breakage) would satisfy it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 records the expected failing node and message per pair (as reproduced at review), and V-04 demands the assertion message. The probe script stays under the gitignored `tmp/`. |
| PR-003 | LOW | IN-SCOPE | G. Stale-comment sweep completeness | `oc_runipd.main` and `agy_runipd.main` `integrate` paragraphs: "while `stop` and `audit` have no such coverage" | E-05's completion check greps only for `2ohbkj`. Both blocks also carry an `integrate` sentence that becomes stale and does not contain that token, so it would survive the edit. The E-01 count of six was also a live count used as a bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 lists the lines, with the count kept only as context. E-05 rewrites the `integrate` clause in both blocks. The outcome and V-05 add an `rg` for the stale phrasings that must exit 1. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate did not frame Scope-Paths as a declaration reconciled at finalize (`--scope-reason`/`--scope-ack`). It stated runner finalize ownership but not "do NOT run it inside the runner", and it omitted the no hand-rolled `git mv` rule and the backlog handoff route. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added each missing element. Also added fixture hygiene to E-02: `support.init_repo`, `TemporaryDirectory`, and an flock released in `finally`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the two non-mutation-sensitive methods be dropped? | Keep them as stderr-discriminating routing characterizations | Drop them (that loses the coverage of unknown-run and unknown-plan routing); redesign them to be exit-code sensitive (no seed makes the rewrite path diverge on exit code without duplicating the other two methods) | Review mutation probe results above | yes |
