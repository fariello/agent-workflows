# Review findings: plan 2a6phj

- Subject-Id: 2a6phj
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `21b22c3b`, which is AFTER the declared dependency `ooydp3` executed
(`aw find plans ooydp3` -> `executed`). That matters: E-01's premise was testable now, so I drove it
rather than deferring to execution. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before any revision. No pre-review snapshot was needed: the lane-input copy at
`.aw/state/lane-inputs/rev-7/` is byte-identical to the tracked file (`diff` -> IDENTICAL) and
`git status --short` was empty.

EVERY AUTHORED FINDING REPRODUCED, and I drove the two that carry the plan rather than trusting them.
F-1, on a scratch repo at the post-`ooydp3` HEAD:

```text
VERDICT legitimate: True | path: HANDOFF | severity: ok
reason: gate 'next' handed off to a From-Backlog plan or spec
carriers: [('.aw/records/plans/pending/...-pl0001-carrier.ipd.md', 'next')]

=== PENDING carrier: rc=0 | item now at ['.aw/records/backlog/done/...item01...']
=== EXECUTED carrier: rc=0 | item now at ['.aw/records/backlog/done/...item01...']
```

So a pending carrier closes a gated item today, and `ooydp3` did not change that (it replaced the gate
comparison with `_same_release`, leaving the arm's shape intact). F-5 also reproduced on one fixture
whose `From-Backlog` pointed at a nonexistent id6, i.e. with NO valid carrier at all:

```text
=== POSITIONAL: backlog set done item01      rc=0 | item dir=['done']
=== --status:     backlog set item01 --status done   rc=1 | item dir=['graduated']
    err: refused: backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate.
```

F-3 and F-4 are verbatim in the shipped text, and F-4's self-contradiction is worse than the plan says:
the backlog README tells authors to close `done` at plan authoring while line 40 of the same file states
that "reaching `done` still requires a handoff, cited evidence, or an explicit de-gate". The design is
sound, OQ-01 is a maintainer ruling I did not revisit, and OQ-03's one-versus-all answer is correctly
reasoned; I confirmed the divergence from the runner's stricter rule is deliberate and documented
(`evaluate_backlog_close` cites `dh0uno`'s two carriers as the measured reason for ALL) and recorded that
so a later reader does not "fix" it.

**THE MOST SERIOUS FINDING IS THAT THE PLAN'S OWN CLOSING INSTRUCTION IS THE CASE ITS RULE POLICES.** The
gate says to close `rwhbci` `done` with `--evidence` citing the executed plan. Measured:

```text
find_from_backlog_artifacts(repo, "rwhbci")
-> .aw/records/plans/pending/20260926-closescope-01-2a6phj-...ipd.md | gate: next | dir: pending
evaluate_blocking_close(repo, <rwhbci>, "done")                  -> True HANDOFF
evaluate_blocking_close(repo, <rwhbci>, "done", evidence=<...>)  -> True HANDOFF
```

`rwhbci`'s ONLY carrier is this plan, so the close is a SELF-CLOSE; and because the `done` branch tests
DE-GATED, then HANDOFF, then SATISFIED, HANDOFF short-circuits and `--evidence` is never read. Today that
close succeeds for precisely the reason this plan calls a defect. After E-03 it falls through to
SATISFIED and depends entirely on the evidence path resolving, which in turn depends on this plan already
being in `executed/`. In a runner lane it is already solved: `runner_shared.evaluate_backlog_close` is
stricter and carries `executed_overrides` for exactly this timing, documented as "a worker asserting a
fact about its OWN item". A hand close before finalize is the exposed case. New E-10 drives both verdicts
and the gate now states the required order (finalize first, then close, `--status` spelling only), with an
explicit prohibition on adding a self-carrier exemption, which would re-open the `x7wfyx` hole.

**THE PLAN'S "`engine.py` NEEDS NO CHANGE (CHECKED)" CLAIM IS FALSE, AND THE STALE TEXT LEAVES THIS REPO.**
It is asserted twice, in E-07 and in the Spec sync section. Measured: `rg -n HANDOFF agent_workflows/engine.py`
HITS, in `_BACKLOG_CLOSE_GATE_PRECOMMIT_TEMPLATE` and `_BACKLOG_CLOSE_GATE_PRECOMMIT_BLOCK`, whose comment
reads "without a preserved-or-satisfied gate (HANDOFF via a From-Backlog plan, DE-GATED, or a persisted
evidence citation)". That text is written into a managed target repo's `.pre-commit-config.yaml`, so
leaving it stale ships the OLD rule definition to every consumer, which is a worse outcome than a stale
line in this repo's own AGENTS.md. `engine.py` is now declared and E-07 gains part (c). I also verified
the managed AGENTS.md prose needs NO change (its "Acting on a backlog item" point (5) already says
"set the item to `graduated`, NOT `done`"), and that `create_backlog_close_gate_hook` is idempotent and
no-clobber, so installed configs are not retro-fixed; E-07 now says that rather than implying a fleet fix.

**THE WARN REMEDY E-05 SETS OUT TO FIX HAS A SECOND, WORSE DEFECT IN THE SAME STRING.** Its `Fix:` line is
`aw backlog set done {_id6}`, the POSITIONAL spelling, which F-5 measures never runs the predicate. So the
advisory currently steers an operator onto the one route that cannot refuse, i.e. it advertises the
bypass. Since E-05 already rewrites that string, correcting the spelling is in scope and does not fix F-5
itself. I also recorded that the warning's index is plans-only (`_iter_plan_ipds`), so a SPEC carrier
never triggers it at all, and told the executor NOT to widen that here.

**THE BLAST RADIUS IS 28 LIVE ITEMS AND THE PLAN STATES NONE.** Enumerated over every `open`/`graduated`
gated item with a carrier: 45 carried, 17 with at least one executed carrier (still closable), 28 that
would now be REFUSED. One of the 28, `ms06pi`, is carried by a spec whose `- Status:` is `approved`, so
E-02 case (4)'s refused half is a shape that exists in the corpus today. Every refusal is the ruling
working as intended, so the number is not an objection; shipping a tightening of this size without anyone
knowing it is the defect. New E-11 re-derives it at execution.

**TWO TEST CASES WOULD HAVE PASSED FOR THE WRONG REASON.** E-02 case (6) (SATISFIED unchanged) asserts only
rc 0, but a `--evidence` close with a pending carrier is allowed TODAY by HANDOFF, so the assertion is
satisfied by the arm this plan is changing; it now asserts the verdict's `path` is `SATISFIED`. And E-06
said to write its before-failing test "if convenient", which is exactly the latitude that turns a
regression test into a tautology; that is now mandatory. I also added case (9), a spec whose directory and
`- Status:` field disagree, so a reader can tell which of the two the rule trusts.

**ONE IMPLEMENTATION NOTE THAT WOULD HAVE BITTEN LATER.** E-03's helper has no status to read:
`find_from_backlog_artifacts` returns `(path, blocks_release)` pairs only. For a plan it must read the
DIRECTORY, and `runner_shared.plan_bucket` is both the precedent and the warning ("a plan STAYS in
`pending/` for its entire non-terminal life", and that function "does no IO and must not learn to"), so a
plan's `- Status:` field cannot identify its bucket while a spec's field is exactly right. The asymmetry is
necessary and now must be explained in the comment. Separately, `aw plans archive` shards `executed/` into
`YYYYMM/`, so the test must match an `executed` SEGMENT; measured, no shards exist today, so a
parent-directory-only test would pass every current test and break on the first archive run.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness; G. executability (a gate instructing a close its own rule polices) | `find_from_backlog_artifacts(repo, "rwhbci")` -> one PENDING path, this plan; `evaluate_blocking_close(repo, <rwhbci>, "done")` -> `True HANDOFF` with and without `--evidence`; arm order DE-GATED/HANDOFF/SATISFIED read in the `done` branch; `runner_shared.evaluate_backlog_close`'s `executed_overrides` docstring | **THE PLAN'S OWN `rwhbci` CLOSE IS A SELF-CLOSE WHOSE LEGITIMACY DEPENDS ON ORDER AND ON ARM PRECEDENCE.** Its only carrier is this plan, and HANDOFF short-circuits before evidence, so today the close succeeds for exactly the reason the plan calls a defect; after E-03 a hand close before finalize depends wholly on the evidence resolving. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low (ordering, not logic) | FIXED | New E-10 drives both verdicts and records the sequence; new OQ-04 resolves it by ORDERING with a self-carrier exemption explicitly rejected; the gate's closing paragraph now prescribes finalize-then-close with the `--status` spelling; new V-10; F-7 records the drive. |
| PR-002 | HIGH | UNDER-SCOPE | A. correctness (a false verified claim; stale managed text shipped to every target repo) | `rg -n HANDOFF agent_workflows/engine.py` HITS at `_BACKLOG_CLOSE_GATE_PRECOMMIT_TEMPLATE`/`_BLOCK`: "HANDOFF via a From-Backlog plan"; that text is written into a target's `.pre-commit-config.yaml`; `create_backlog_close_gate_hook` is idempotent/no-clobber | **THE PLAN ASSERTS TWICE, AS VERIFIED, THAT `engine.py` CARRIES NO HANDOFF DEFINITION. IT DOES**, in managed pre-commit templates installed into every managed repo, so the old rule definition would keep shipping outward. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `agent_workflows/engine.py` added to `- Scope-Paths:`; E-07 gains part (c) for both template constants plus the statement that installed configs are not retro-fixed; the Spec sync section's false claim replaced with the measurement; V-07 requires the before/after grep and forbids re-asserting "no managed text changes"; F-8. |
| PR-003 | HIGH | IN-SCOPE | B. security-adjacent (an advisory that steers onto the bypass) | the message string `Fix: aw backlog set done {_id6}` read in `release_gate_warnings`; driven with NO valid carrier: positional rc 0 + item moved to `done/`, `--status` rc 1 with the three fixes | **THE WARN REMEDY NAMES THE POSITIONAL SPELLING, WHICH F-5 PROVES SKIPS THE PREDICATE.** So the repository currently advises the one close route that cannot refuse, which would let an operator close an item this plan exists to hold open. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | E-05 must emit `aw backlog set <id6> --status done`; V-05 requires the corrected string plus the driven bypass proof; recorded as in scope because E-05 already rewrites that string, and explicitly NOT a fix for F-5 itself (still Deferred, carried by E-09); F-9. |
| PR-004 | MEDIUM | UNDER-SCOPE | C. operability (an unstated tightening of live state) | enumeration over `backlog._iter_items` (`open`/`graduated` + `Blocks-Release:`) resolved through `find_from_backlog_artifacts`: 45 carried, 17 with an executed carrier, 28 refused; `ms06pi` carried by `specs/approved/...spec.md` with `- Status: approved` | **28 LIVE ITEMS WOULD BECOME UNCLOSABLE AND THE PLAN STATES NO BLAST RADIUS.** Each refusal is intended behavior, but the size is material to an approving human and to whoever next tries a close. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | New E-11 re-derives the classification with counts and the refused list; new V-11; the gate names the figure as the first thing to look at; F-10 records the measurement and the `approved`-spec case. |
| PR-005 | MEDIUM | UNDER-SCOPE | E. testing (two cases that pass for the wrong reason) | HANDOFF precedes SATISFIED, so `--evidence` + pending carrier is allowed today by HANDOFF; E-06's "if convenient" latitude | **E-02 CASE (6) IS VACUOUS AS WRITTEN AND E-06's BEFORE-FAILING TEST WAS OPTIONAL.** Asserting rc 0 for the SATISFIED case proves nothing about which arm allowed it, and a regression test written only after the fix cannot distinguish "the rule follows" from "the fixture never triggered it". | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Case (6) now asserts the verdict `path == "SATISFIED"`; E-06's before-failing run is mandatory; V-02 requires `-v` per-node output and names the two easy-to-fake assertions; the gate's honesty rule lists all three driven claims. |
| PR-006 | MEDIUM | UNDER-SCOPE | A. correctness (a helper that cannot read what the item assumes) | `find_from_backlog_plans`/`_specs` both build `(p, mbr.group(1) if mbr else "")`, no status; `plan_bucket`'s docstring on `pending/` and on doing no IO; `.aw/records/plans/executed/` holds no shard dirs today | **THE CARRIER LOOKUP CARRIES NO STATUS, AND THE PLAN-VS-SPEC READERS MUST DIFFER.** E-03 says `_status_meta` for specs but never states that a plan's `- Status:` cannot identify its bucket, nor that `executed/` can be sharded into `YYYYMM/`, so a parent-directory test would pass today and break on the first archive. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now specifies re-reading each file, directory-for-plans and field-for-specs with the asymmetry explained in the comment, and an `executed` SEGMENT match for shard safety; F-11; the conventions section records all three facts. |
| PR-007 | MEDIUM | IN-SCOPE | E. testing (a live shape not pinned) | `ms06pi` is `graduated`, gated `next`, sole carrier `specs/approved/...spec.md` with `- Status: approved` | **E-02 CASE (4) PINS approved-vs-implemented BY DIRECTORY ONLY**, while the rule reads the FIELD and a real corpus item has an `approved` spec carrier. A directory/field mismatch had no case at all. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (4) must assert the `approved` refusal by field; new case (9) covers a directory/field mismatch; V-02 calls out case (4); F-10 records the live example. |
| PR-008 | LOW | IN-SCOPE | G. executability (a stale premise and an unmeasured before-state) | `ooydp3` measured `executed`; F-1 reproduced post-`ooydp3`; `aw check release-gates --agent` -> `conforms`, `findings: 0`, exit 0 | **E-01's STOP CONDITION AND E-08's BEFORE-STATE WERE BOTH UNMEASURED.** The plan told the executor to stop if the close is already refused (it is not, post-`ooydp3`), and E-08 allowed any after-finding to be read as possibly pre-existing when the before-state is in fact clean. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records the review measurement and the arm order and says not to expect the stop; E-08 states the clean before-state, requires item-by-item explanation of any after-finding, and notes the rule is commit-scoped so E-11's 28 items do not appear in that sweep; V-08 updated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The gate instructs closing `rwhbci` `done`. Accept it, or check whether the new rule permits it? | CHECK, and it is order-dependent: the only carrier is this plan and HANDOFF precedes evidence. Prescribe finalize-then-close and drive both verdicts. | (a) Accept as written: rejected, an executor following it before finalize could be refused, or could succeed for the pre-fix reason, and neither is a legitimate close under the rule this plan ships. (b) Exempt a self-carrier in the predicate: rejected outright, that re-opens the `x7wfyx` failure (closed citing a plan that had not run), which is the entire defect. (c) Close via `--evidence` only and ignore ordering: rejected, evidence must resolve to a path that exists, and the executed path does not exist until finalize moves it. | Both verdicts driven; the `done` branch's arm order read; `evaluate_backlog_close`'s `executed_overrides` rationale read. | yes |
| D-2 | The plan says `engine.py` carries no HANDOFF definition. Trust the stated check, or re-grep? | RE-GREP, and it does: the managed pre-commit templates. Declare `engine.py` and update both. | (a) Trust it: rejected, and the cost of being wrong is asymmetric, since managed text is installed into every target repo, so a stale definition propagates outward rather than sitting in one file. (b) Change the hook's behavior too: rejected, the hook delegates to the predicate and needs no logic change; only its DESCRIPTION is stale. (c) Migrate already-installed configs: rejected as out of scope and stated as a limit, since the installer is no-clobber by design. | `rg -n HANDOFF agent_workflows/engine.py`; both template constants read; `create_backlog_close_gate_hook` read for idempotence. | yes |
| D-3 | E-05 rewrites the WARN remedy for staleness. Is staleness the only defect in that string? | NO: it also names the POSITIONAL spelling, which bypasses the predicate. Correct both in the same edit. | (a) Fix only the staleness: rejected, it would leave the repository advertising the exact bypass F-5 documents, on the surface an operator is most likely to copy. (b) Fix F-5 itself here: rejected, it is a separate dispatch-path defect with its own tests, the plan defers it deliberately, and E-09 files it as a durable carrier. | The message string read; both spellings driven on one fixture with no valid carrier. | yes |
| D-4 | Should the review measure the corpus impact the plan omits? | YES, and report it: 45 carried, 17 closable, 28 newly refused, one via an `approved` spec. | (a) Leave it unmeasured: rejected, an approving human cannot weigh a tightening whose size is unknown, and the first person refused a close would discover it as a surprise. (b) Treat the 28 as a blocker: rejected, every one is the ruling working as intended (code has not shipped, item stays `graduated`), so disclosure is the correct response, not a veto. | Live enumeration over the backlog and plans/specs trees; `ms06pi`'s carrier read. | yes |
| D-5 | E-02 case (6) asserts rc 0 for the SATISFIED case. Sufficient? | NO: assert the verdict `path`. Today rc 0 comes from HANDOFF, the very arm being changed. | (a) Keep rc 0 only: rejected, the case would pass before and after while proving nothing about SATISFIED, and would silently mislead if E-10 ever reorders the arms. (b) Reorder the arms so SATISFIED precedes HANDOFF: rejected as an unrequested behavior change; the ruling touches HANDOFF only, and the reorder is recorded as E-10's question rather than done silently. | Arm order read; the interaction driven (evidence ignored while HANDOFF matches). | yes |
| D-6 | E-03 says specs use `_status_meta`. Does the same reader work for plans? | NO. Directory for plans, field for specs, and the difference must be explained; plus shard-safe segment matching. | (a) Read `- Status:` for both: rejected, measured wrong by `plan_bucket`'s own docstring, since a plan sits in `pending/` through `approved`, so a `- Status: approved` plan would be read as non-executed correctly but a `- Status: executed` hand-edit would be trusted over its directory. (b) Use `is_retired`: already rejected by the plan for the right reason (it is True for `superseded`/`not-executed`/`parked`/`done`). (c) Match only the parent directory: rejected, `aw plans archive` shards `executed/YYYYMM/`, so it would pass today and break on the first archive. | Both `find_from_backlog_*` bodies read; `plan_bucket` docstring read; `executed/` inspected for shards. | yes |

### Deferred and open

- (none). All eight findings were FIXED in place. Three sit at the `HIGH` gate threshold (PR-001,
  PR-002, PR-003) and each is fixed WITHIN this plan's scope, so no `- Blocking: yes` escalation is
  owed. F-5 (the positional bypass) remains correctly DEFERRED and is not this plan's to fix; PR-003
  only stops the repository from ADVERTISING it, and E-09 files it as a durable carrier so the
  obligation survives. OQ-01 through OQ-03 were already resolved and I confirmed rather than re-opened
  them; I added OQ-04 (resolved, non-blocking) because the plan's own close needed a recorded answer
  rather than an implicit one.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECTS, the arm order,
the managed-text exposure, the bypass spelling, and the corpus impact by driving them; I did NOT
implement the change, so that `_carrier_is_executed` lands correctly for both artifact kinds, that no
E-02 case regresses, and that the `rwhbci` close sequence actually works remain E-03, E-10 and their
validation. My blast-radius figure counts items whose carriers I classified by DIRECTORY for plans and by
`- Status:` for specs, which is the rule E-03 will implement; if E-03 implements it differently the count
moves, which is why E-11 re-derives rather than inheriting my number. I did not run the bare suite
against a patched tree, so E-08 remains a real obligation. And I did not audit whether any other pending
plan edits `evaluate_blocking_close`; `ooydp3` (the declared dependency) has executed, but a concurrent
plan touching the same arm would be an unmeasured collision of the kind that bit a sibling plan in this
same sweep.
