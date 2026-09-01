# Review: Host-neutral run-as dispatch and default runner routing

- Plan-Id: ygzq71
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `6a29f9c0`, working tree clean, plan committed and unchanged. Structural preflight
`aw ipd lint --phase author` reports `conforming`.

This child is where the `0soncw` conflict is sharpest, and it is worth being precise about why, because
the plan is NOT naive about collisions: it identifies the hazard correctly and then solves the wrong half.

Its Concern states "`aw run` already owns a substantial fixed run-ledger command family. Treating profile
names as dynamic top-level or run subcommands would collide", and its Project-conventions note repeats that
"Dynamic subparsers are incompatible with the user's no-collision requirement". Both TRUE and well
reasoned. Its answer is a FIXED grammar (`aw run as` / `aw run ipd`) registered, per E-01, "under the
existing run family".

But the collision it defends against is a profile name shadowing a ledger subcommand, whereas the actual
hazard is that APPROVED `0soncw` DISMANTLES that family: it moves every `aw run` subcommand under
`aw runs` and leaves `aw run` as a nonzero-exit deprecation stub. So E-01 registers new entries under a
parser family that is scheduled to be emptied. Fixed-versus-dynamic does not address that at all.

The Set-wide BLOCKER (PR-001, the `0soncw` ordering conflict) is recorded on every member because it
affects each one's executability, but it is ESCALATED once, as a blocking open question on the
orchestrator `3m0urk`, which owns cross-Set sequencing. Six copies of one question would be six places
to answer it inconsistently.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | B. Sequencing / G. Plan executability | APPROVED `0soncw` ("Collapse run inspection under aw runs and retire the aw run noun"); its E-05 (`:103-108`) keeps `aw run` only as a deprecation stub returning a NONZERO exit and a message naming `aw runs`; its Scope-Paths include `cli.py`, `completion.py` and `command_surface.py`. Measured across this Set: `aw run as` x16, `aw run ipd` x12, and `grep -rln '0soncw\|runnamecollapse'` over all six plans returns NOTHING. | This plan builds on the `aw run` noun that an APPROVED plan is retiring, and the Set never mentions that plan. They are COMPLEMENTARY, not contradictory: `0soncw` retires the noun explicitly "so the name is free for a future driver verb", and this Set IS that verb, so the fix is ORDER (`0soncw` first, then this Set claims the vacated name). Reversed, `0soncw`'s stub would shadow a namespace this Set had just populated and `aw run as <profile>` would start exiting nonzero. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | OPEN | Cross-Set execution order is the maintainer's decision and `0soncw` itself still carries an unresolved BLOCKING OQ-03, so the prerequisite is not executable yet either. Escalated as a blocking OQ on the orchestrator `3m0urk` (the owner of cross-Set sequencing) rather than duplicated as six separate questions. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness (evidence discipline) | Measured citation counts: this Set has **0** `file:line` citations in ALL SIX plans, versus 9 / 4 / 5 in the comparable `6lu3rq` / `m73aet` / `wlxkoz` plans reviewed the same day. | The Set asserts many things about shipped code ("`cli.py` already registers `aw run` as the run-ledger family", "`oc_models.resolve_config_path()` already mirrors OpenCode configuration discovery") without a single line citation. The claims I spot-checked were TRUE, so this is an evidence-discipline defect rather than a correctness one, but it means an executor cannot re-verify a premise cheaply and cannot tell whether a claim was measured or remembered. That matters most here because the Set edits `cli.py` and `oc_runipd.py`, the two most contended files in the repo. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added a Findings row to each plan recording the gap and requiring the executor to MEASURE and cite `file:line` for every "already" claim before relying on it, since HEAD moves hourly here. |


### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Escalate the `0soncw` conflict on this child, or once on the orchestrator? | ONCE on the orchestrator `3m0urk`, recorded as a finding here. | Raising a blocking OQ on all six children. Rejected: one cross-Set ordering decision answered in six places invites six inconsistent answers, and the orchestrator is the artifact that already owns Set-level sequencing (it carries CID-8 for `rununify`). | `3m0urk`'s existing CID-8 and its "STOP and re-review all runner scopes" clause; plan-review Step 2.4 ("fix it in the owning plan and cross-reference it from dependent plans") | yes |
| D-2 | Is the missing `file:line` evidence (PR-002) a BLOCKER or a MEDIUM? | MEDIUM. The claims I spot-checked were true, so this is evidence discipline, not incorrectness. | BLOCKER. Rejected because no verified claim was found to be false, and blocking a Set on citation formatting when its substance holds would be disproportionate. | Spot-checks: `oc_models.resolve_config_path` exists; `aw oc run --help` genuinely lacks `--variant`; `cli.py` genuinely registers the `aw run` family | yes |
