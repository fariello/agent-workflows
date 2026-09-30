# Review findings: plan zyj8io

- Subject-Id: zyj8io
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-C01 (HIGH, fixed), PR-C02 (MEDIUM, fixed), PR-C03 (MEDIUM, fixed), PR-C04 (MEDIUM, fixed), PR-C05 (MEDIUM, fixed), PR-C06 (HIGH, open, escalated to OQ-02)

## Round 1

Reviewed in an isolated review lane at HEAD `3b4655ab`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author` reported `conforming` BEFORE semantic review. The plan is `- Kind: child`, so
the `IPD-S407` orchestrator row check does not apply. `- Item-Dependencies: none`. Suite at review, bare:
`3387 passed, 2 skipped in 58.06s`.

ALL NINE AUTHORED FINDINGS REPRODUCE. I re-drove every one rather than trusting any:

- F-1 exactly, all four surfaces: `find plans zzzzzz` gives `✓ CLEAN no matching plans` exit 0; `--agent`
  gives `outcome:clean,exit:0`; `--json` gives `status:clean,exit_code:0`; `--paths` gives empty stdout
  exit 1. The three-way split is real.
- F-2 exactly: `find plans reusable` exits 0 with no rows, and `.aw/records/plans/reusable/` holds only
  `README.md`. Worth adding what the plan did not say: `selectors.resolve(root,"plans","reusable")`
  returns `kind=None` with zero paths, which is byte-for-byte the same resolver answer as the typo
  `zzzzzz`. So the vocabulary predicate is not a nicety, it is the ONLY thing that can separate these two
  cases, since the resolver cannot. I drove the full design end to end (union vocabulary plus match fact)
  and it does separate them correctly: `reusable` -> exit 0 (vocab), `zzzzzz` -> exit 2.
- F-3 exactly, to the token: vocabulary size 74, `ARTIFACT_TYPES` members absent are `['reviews','other']`,
  and the only status absent from the 25-value union is `intake`.
- F-4 exactly: Section 11.1 mandates `exit: 0` for an empty read result; Section 12 states "If a specific
  selector matches zero paths, the command exits `1`". Both are normative prose in the same document.
- F-5 exactly: the `89bby9` record sits under "Clean empty query result (`exit: 0`)".
- F-6 confirmed by driving, not only by reading: `_find_type_records("plans",["zyj8io"])` returns 1 line
  and `matches=['zyj8io']`; adding `status="executed"` returns 0 lines and STILL `matches=['zyj8io']`. So
  the pre-narrowing fact the plan requires already exists in the shipped `_FindMatch` thread, which makes
  E-03 smaller than it reads.
- F-7 confirmed: `pending` resolves `kind='substring'` with 6 paths, so a substring-only query does match
  and keying on RESOLVED would indeed refuse it.
- F-8 exactly: `aw ipd board zzzzzz` exits 2 with `unrecognized arguments: zzzzzz`.
- F-9 confirmed at the cited expression.

I also confirmed both cited precedents behave as claimed: `aw runs zzzzzz` and `aw attention zzzzzz` both
exit 2, and `attention`'s `--agent` refusal carries `unresolved_selectors`, `unresolved_targets` and
`error`.

THE ONE FINDING THAT WOULD HAVE SHIPPED A REFUSAL SAYING NOTHING.

PR-C01. E-04 requires a `cannot-run` record "naming each unmatched token", matching `unresolved_targets`.
Measured, that is unreachable by the route E-04 implies. `result_types.CommandResult` has no
`unresolved_targets` field, and `CommandResult.to_agent_record` composes a FIXED key set, so a token
placed in `data` is silently dropped on the `--agent` surface. I built the exact record E-04 describes and
emitted it: `{"schema":...,"outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":0,
"next":null}` with the token nowhere in it. The exit code and outcome would have been right and the
diagnostic value would have been zero, which is most of what the plan is for. Three further measurements
make the fix concrete rather than a complaint: the schema ACCEPTS the extra keys (I validated a
find-shaped record carrying all three of attention's fields), `attention._unresolved_selector_record`
hand-builds its dict precisely to get them, and `--json` DOES render `data` verbatim, so the two machine
surfaces genuinely differ and must be handled separately rather than assumed symmetric.

FOUR MORE FINDINGS OF SUBSTANCE.

PR-C02. E-08 says to enumerate the survey population "from the argument parser rather than by memory",
which sounds like a bound and is not one. Walked recursively, `cli._build_parser()` has 187 leaves
carrying a positional argument, 33 at top level. Probing each on every surface is a plan of its own, and
an item whose size is unstated is an item an executor either under-delivers or disappears into.

PR-C03. The plan declares `tests/test_cli_find.py` (3 tests) and never mentions
`tests/test_find_filters.py` (11 tests), whose own docstring says it "define[s] the behavioral contract
that spec 4sd62s's SQLite-cache rewrite of aw find must preserve" and four of whose cases assert `rc == 0`
on a `-p` zero-or-few-row query. This is a finding with a REASSURING answer, which is why it is MEDIUM and
not HIGH: I checked each of those four and all eleven tests survive this plan unchanged, because each one
either passes no selector (so the shipped `not selectors` exemption applies) or passes a selector that
matches. So no scope change is warranted. What was missing was that anyone had checked: a plan changing
`-p` exit codes that does not know where the `-p` contract is pinned is one measurement away from
discovering it by breaking it.

PR-C04. E-05 and E-06 argue for stderr by importing `attention`'s convention, and the plan never notices
that `_run_find` ALREADY CONTAINS a four-surface exit-2 refusal doing exactly this. Its `--status`
validation block emits `CommandResult(status="cannot-run", exit_code=2)` on machine surfaces, writes
through `Term(stream=sys.stderr, ...)` on the `--paths` branch with the comment "stdout stays empty so a
-p consumer sees no path; write refusal to stderr", and uses `term.status("fail", ...)` for humans. Driven,
all four surfaces answer 2. This matters twice: it makes the new refusal a local pattern match rather than
a cross-module import, and it RESOLVES OQ-01 from evidence, since the question "stdout or stderr" is
already answered inside the function being edited.

PR-C05. F-5's framing of the doc example is incomplete in a way that would have produced a wrong fix. The
`89bby9` example is not merely about to become stale; it is FALSE TODAY, independently of this plan.
`89bby9` is a live id6 (the executed plan `20260822-highpbacklog0822-04-89bby9-...`), so
`find plans 89bby9 --json` answers `count: 1`, not the `count: 0` the document prints. An executor reading
E-07 as written would re-label that record as a refusal and leave a MATCHING selector illustrating "no
match".

THE FINDING I COULD NOT FIX, AND WHY I DID NOT PRETEND TO.

PR-C06 / OQ-02. The `--paths` exit code change from 1 to 2/0 is the one irreversible decision in the plan.
`--paths` is the explicitly script-shaped surface, its exit classification is published in
`docs/cli-output-contract.md` Section 12, and an out-of-tree consumer branching on exit 1 cannot be
enumerated from inside this repository, let alone fixed. Step 3.1 of this workflow says a `Reversible: no`
decision must not rest on the reviewer's authority alone, and this run had no interactive channel, so
recording my own preference as the answer would have been exactly the forged attestation the plan's own
gate paragraph warns about. I escalated it to `Blocking: yes` with `Owner: maintainer` and a
`- Finding: PR-C06` back-reference, which is the mechanism that actually stops execution: `aw ipd lint`
now reports `IPD-Q501` at `review-finalize` and will at every other checkpoint. What I DID do is make the
decision cheap to take: nothing in this repository branches on that exit code (searched `agent_workflows/`,
`tools/`, `.aw/system/`, `.opencode/`, `.claude/`), the only documented statement of the current behavior
is the self-contradicting sentence the plan already corrects, and the narrower alternative is separable at
no cost because E-06 is its own item and E-08's table already carries the deferral record.

WHAT IS STRONG. The authoring measurement discipline is genuinely high: nine findings, all nine
reproducible, several of them facts the backlog item did not know, and two of the item's own premises
corrected by measurement rather than inherited. The `reusable` exemption in F-2 is the kind of case most
fail-closed changes discover in production, and finding it before writing code is why this plan is close
to executable. E-01's insistence on a characterization test that must fail before the fix lands is right,
and V-01 enforces it. The five `Carrier-Declined` rows argue from measurement rather than convenience, and
F-8 answers a backlog item's suggestion with a probe instead of an opinion. None of my findings weakened a
`V-*`; five strengthened one.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-C01 | HIGH | IN-SCOPE | Rubric A (correctness), E (evidence), G (executability) | plan E-04 and V-04; `result_types.CommandResult` fields and `to_agent_record`; the record driven at review; `attention._unresolved_selector_record`; `agent_schema.assert_valid_agent_record` | E-04 promises a `cannot-run` record "naming each unmatched token" via `unresolved_targets`. `CommandResult` has no such field and `to_agent_record` composes a FIXED key set, so a token in `data` is SILENTLY DROPPED on `--agent`. Driven: the exact record E-04 describes emits with `findings:0, next:null` and no token anywhere, i.e. a refusal that does not say what failed. The two machine surfaces also differ: `--json` renders `data` verbatim, `--agent` does not. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Recorded as F-10 and F-11. E-04 now forbids the `CommandResult` route for `--agent`, points at `attention`'s hand-built dict plus the schema validator (driven at review to accept the extra keys), and treats the two machine surfaces separately. V-04 fails the item if the token is absent from the EMITTED BYTES rather than merely passed in. |
| PR-C02 | MEDIUM | IN-SCOPE | Rubric G (executability, right-sizing) | plan E-08; recursive walk of `cli._build_parser()` | "Enumerate them from the argument parser" is not a bound: 187 parser leaves carry a positional argument, 33 at top level. Probing each on every surface is a plan of its own, and an unstated population makes a closeout item either under-delivered or unbounded. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-12. E-08 now states three filters (read-only, artifact-selector, tree-resolving), requires the surviving count be recorded BEFORE probing, and caps the item by filing one backlog item for any unmeasured remainder. V-08 fails the item if the population is unstated. |
| PR-C03 | MEDIUM | UNDER-SCOPE | Rubric D (anti-regression), E (testing) | `tests/test_find_filters.py` docstring and its four `-p` zero-row cases, all driven; plan `- Scope-Paths:` | The verb's real behavioral-contract module (11 tests, self-described as the contract a future rewrite must preserve, four cases asserting `rc == 0` on a `-p` zero-row query) is neither declared nor mentioned, in a plan whose whole subject is `-p` exit codes. Measured, all 11 SURVIVE unchanged (each of the four passes no selector or a matching one), so no scope change is warranted; what was missing was that anyone had checked. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-13. The validation section now requires its full passing run as evidence and declares a failure there a STOP condition rather than a test to update; E-06 names the four surviving cases and why they survive. The file stays outside the fence deliberately. |
| PR-C04 | MEDIUM | IN-SCOPE | Rubric C (use existing mechanisms), F (KISS) | `cli._run_find`'s `--status` validation block; all four surfaces driven at review | E-05/E-06 argue for the stream split by importing `attention`'s convention, while `_run_find` ALREADY CONTAINS a four-surface exit-2 `cannot-run` refusal drawing exactly that split (machine `CommandResult`, `--paths` to `sys.stderr` with the reason in a comment, human `term.status("fail", ...)`). Driven: all four answer 2. Missing it costs a needless cross-module import and risks two refusals drifting inside one function. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 and E-06 now cite the in-function precedent as the shape to copy, with the driven measurement. This also RESOLVES OQ-01 from evidence rather than as a taste call. |
| PR-C05 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy; Rubric G | `docs/cli-agent-protocol.md` example; `find plans 89bby9 --json` driven; the executed plan owning that id6 | F-5 treats the `89bby9` example as about-to-become-stale. It is FALSE TODAY: `89bby9` is a live id6 and the command answers `count: 1`, not the printed `count: 0`. An executor following E-07 as written would re-label that record as a refusal and leave a MATCHING selector illustrating "no match". | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-14. E-07 now requires REPLACING the token with one that genuinely matches nothing, and requires keeping a real `count: 0` clean example so Section 11.1's surviving half stays illustrated. V-07 fails the item if the `89bby9` token survives. |
| PR-C06 | HIGH | IN-SCOPE | Rubric A (public contract), B/C (compatibility) | plan E-06 and OQ-02; `docs/cli-output-contract.md` Section 12; repository-wide search for a consumer branching on `aw find -p`'s exit code | The `--paths` exit code change from 1 to 2/0 is IRREVERSIBLE for out-of-tree consumers and alters a PUBLISHED exit classification, yet OQ-02 carried `Blocking: no` with `Owner: reviewer`. A reviewer may not authorize an irreversible public-contract change on their own authority, and this run had no interactive channel, so resolving it would have recorded a preference as an attestation. | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED, not fixed: OQ-02 is now `Blocking: yes`, `Owner: maintainer`, carrying `- Finding: PR-C06`, so `aw ipd lint` reports `IPD-Q501` at every checkpoint and the plan cannot reach `approved` until a human answers. The decision was made cheap to take: the review records that NOTHING in this repository branches on that exit code, that the only documented statement of the behavior is the self-contradicting sentence the plan already corrects, and that the narrower alternative is separable at no cost. The gate paragraph states all of this for the maintainer. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: should the human-surface refusal go to stdout or stderr? | STDERR, resolved at review from in-repository evidence rather than left for a human. | Stdout, rejected: it would leave ONE function refusing two different ways, since the `--status` refusal in the same function already writes to stderr. Leaving the question open, rejected: the repository already answers it, and this workflow forbids asking a human what the repository answers. | `cli._run_find`'s `--status` block: machine `CommandResult(status="cannot-run", exit_code=2)`, `--paths` through `Term(stream=sys.stderr, ...)` with the comment "stdout stays empty so a -p consumer sees no path; write refusal to stderr", human `term.status("fail", ...)`. Driven: `aw find plans --status bogus` exits 2 on all four surfaces. | yes |
| D-2 | E-04 cannot emit the token through `CommandResult`. Extend `CommandResult` with an `unresolved_targets` field, or hand-build the `--agent` record as `attention` does? | HAND-BUILD, following `attention._unresolved_selector_record`. | Adding a field to `CommandResult`: rejected as a change to the shared result type every verb in the CLI renders through, which is a far larger blast radius than this plan's fence and would need its own review; `to_agent_record`'s fixed key set would also have to learn the field. Leaving E-04 as written: rejected, it ships a refusal naming nothing. | The record driven at review (token dropped); `agent_schema.assert_valid_agent_record` ACCEPTING a find-shaped record with `unresolved_selectors`/`unresolved_targets`/`error`; `attention`'s own hand-built dict plus validator call, which exists for this exact reason. | yes |
| D-3 | `tests/test_find_filters.py` pins the `-p` contract and is not declared. Add it to `- Scope-Paths:`? | NO. Leave it outside the fence and require its passing run as evidence instead. | Declaring it: rejected because measurement shows it needs no edit (all 11 tests survive), and declaring a file the plan will not modify would trip the finalize scope gate's declared-but-unmodified reconciliation. Saying nothing: rejected, a plan changing `-p` exit codes must know where the `-p` contract is pinned. | Each of the four `-p` zero-row cases read and classified: `specs --status to-review -p`, `specs --id spc001 -p`, `backlog --set setgamma -p`, `walkthroughs --status anything -p` all pass NO selector (the shipped `not selectors` exemption); `specs setalpha --status approved -p` passes a MATCHING selector. Full module run: 11 passed. | yes |
| D-4 | OQ-02 is an irreversible published-contract change. Resolve it with the reviewer's judgement, or escalate? | ESCALATE to `Blocking: yes` / `Owner: maintainer`, and leave the finding OPEN. | Resolving it myself as acceptable: rejected on the explicit rule that a `Reversible: no` decision must not rest on reviewer authority alone; the plan's own gate paragraph also forbids writing an attestation for a role one is not performing. Telling the maintainer directly instead of escalating in-plan: not available, this run has no interactive channel, which is precisely the case the rule says to handle with a blocking question. | `docs/cli-output-contract.md` Section 12 publishes the exit classification; repository-wide search found NO in-tree consumer branching on it, so the risk is entirely out-of-tree and unenumerable; `aw ipd lint` now reports `IPD-Q501`, verifying the escalation actually gates. | no |

D-4 is the round's only `Reversible: no` decision and it is ESCALATED rather than merely recorded, which
is what that classification requires: OQ-02 now carries `- Blocking: yes` and `- Finding: PR-C06`, and the
lint gate refusing the plan at `review-finalize` was verified after the edit. OQ-01 is `resolved`.
PR-C06 is the only finding left OPEN and it is at or above the repository's `HIGH` gate threshold, which
is why it is escalated into the plan as a blocking question rather than reported in prose alone.
