# Review: Stamp AW-Run and AW-Item trailers on the agent's own aw commit calls inside a run

- Subject-Id: a6xbso
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe9469d8` (the plan was authored at `61ef21d8`, an ancestor). The target plan was
committed and unchanged, so the pre-review snapshot was correctly skipped per Step 1. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review and
`--phase review-finalize` reported `conforming` after the edits, including the added E-08/V-08.
`aw check plans --agent` reports no finding against this plan and
`check_engine.evaluate_durable_carrier` returns `[]`.

THE DIAGNOSIS IS RIGHT AND THE DESIGN IS THE CORRECT ONE. I reproduced the central claim rather than
reading it: in a scratch repo with both env vars exported,
`python3 -m agent_workflows commit --no-plan -m x -- f` commits a message of exactly `x` with both
trailer fields empty (`git log -1` -> `'x\n|||\n'`). F-2 therefore holds precisely, and the diagnosis of
WHY is exact: `_trailers_from_args` reads only `args.trailers`/`args.run_id`/`args.item_id6`, and no CLI
flag sets any of them. F-3 holds in both hosts: each `child_env = pinned_child_env()` block sets only
`EXECUTION_ROLE_ENV` and pops `DRIVER_ATTEST_ENV`. F-4 holds: the runbook's directive 4 does direct
`aw commit`, so the channel is the only missing piece. `state` and `item` are both in scope at each
block, so no plumbing is needed. The plan's decision to leave `pinned_child_env` generic is also
correct and I checked it: that function is bound as an `env_builder` by several driver-side call sites
where a per-turn item id would be wrong.

THE FINDING MOST LIKELY TO HAVE BITTEN THE EXECUTOR IS PR-1201, AND THE PLAN NAMED THE WRONG TEST. F-5
warned that a suite run inside a turn would stamp trailers onto scratch commits, citing "the
byte-identity assertions in `tests/test_git_commit_helper.py`". Those assertions call
`git_commit_helper.offer_commit` DIRECTLY with an explicit `trailers=` argument and never reach
`_trailers_from_args`, so they are unaffected. The test that genuinely breaks is in the same file and is
sharper: `test_aw_commit_threads_trailers_and_lifecycle_delegates` asserts literally
`work_cmd._trailers_from_args(argparse.Namespace()) == []`. Driven at review with the env patched and
the E-03 fallback prototyped, that call returns
`['AW-Run: run-20260926T010203Z-4242', 'AW-Item: abc123']`, so the assertion FAILS. The conftest scrub
is what keeps it green, which means E-06 and that test are COUPLED and the coupling was unstated, with
the file undeclared in `- Scope-Paths:`. Both are now fixed, and V-06's reverted run must name that
assertion as one of the failures, because the scrub's effect is invisible in any run not launched with
the vars exported.

THE SECOND FINDING IS THAT NOTHING IN THE PLAN PROVED THE TWO HALVES AGREE. Case (1) exercises the
reader through a real `aw commit` but sets the env BY HAND, so it never touches the writer. Cases (5)
and (6) exercise the writer but assert only on the captured env dict. So the contract this plan exists
to deliver, that what the runner EXPORTS is a value `aw commit` ACCEPTS, was asserted nowhere. That
matters more than it would in most plans because the two sides validate against two SEPARATE
definitions of the run-id shape by deliberate choice: E-03 defines a local pattern rather than
importing `runner_shared`, for the good reason that importing the runner into every `aw commit` would
be absurd. Two independent definitions of one format is exactly the pair that drifts silently. I added
E-08/V-08: capture the writer's exported value and feed THAT string through the reader, for both the
plain `new_run_id` shape and the `-N` collision suffix.

THE THIRD IS A TRAP INSIDE THE HARNESS THE PLAN TELLS THE EXECUTOR TO REUSE.
`tests/test_driver_attestation_gate.py::test_child_env_scrubs_driver_attest_for_both_hosts` builds
`state = {"run_id": "run-test", ...}`. `run-test` FAILS the run-id pattern E-03 validates against,
while its `id6: "abc123"` is valid. Because the write side deliberately does not validate, cases (5)
and (6) will PASS while asserting `AW_RUN_ID=run-test`, a value the reader would drop. That is
self-consistent, not contradictory, but it means those cases prove EXPORT and not USABILITY, and the
plan said nothing about it. Worse, an executor who noticed the mismatch might "fix" it by adding
validation to E-04/E-05, which would be the wrong half and would then make the reused harness fail. I
recorded the measurement (all 283 real run dirs match the pattern; `run-test` does not), told the
executor to either keep the value and document it or use a valid one in their own copy, and explicitly
forbade adding write-side validation.

I ALSO MADE THE WRITE-SIDE ASYMMETRY EXPLICIT RATHER THAN LEAVING IT TO BE INFERRED. The plan places
validation only at the reader, which is correct (a runner that silently dropped its own id would make
a real run indistinguishable from no run), but it never said so, and an asymmetry with no stated reason
reads as an oversight to the next maintainer. E-04 and the gate now state it and its consequence.

TWO CORRECTIONS OF FACT AND ONE PRE-EXISTING DEFECT I DID NOT FIX. The plan names the Order 2 artifact
`am1g38` throughout, which is the BACKLOG item; the Order 2 PLAN is `199u11`, which carries
`- Item-Dependencies: executed:a6xbso` and `- From-Backlog: am1g38`. A reader following `am1g38` as a
plan id finds nothing, so I corrected the Goal, Scope and Deferred while leaving the `- Carrier:` field
pointing at the item (correct: the carrier vocabulary resolves backlog and plans, and the item is the
durable obligation). F-6 called `8apjpp` "pending" when it is `executed` and its trailers are already in
the tree, which the plan's own Deferred section says two paragraphs later. And `conftest.py` carries a
STALE CROSS-REFERENCE, twice, to `tests/test_role_declaration_guard.py`, which does not exist anywhere
in the tree; that predates this plan and is unrelated to trailers, so I recorded it as INFO rather than
widening scope, with a note not to copy the pattern of citing a nonexistent test.

THE CORPUS COUNTS HAVE ALREADY DRIFTED, WHICH IS A LIVE-ARTIFACT PROBLEM AND NOT AN ERROR. The Concern
and F-1 assert "188 commits, exactly ONE trailered" and "39 across all refs". Re-measured at review:
206 commits with 1 trailered, and 71 across all refs. The PROPERTY held at both measurements and is
what the plan actually needs: the trailered set is overwhelmingly driver-side `closed by aw oc run`,
and I checked the 9 `work(...)` commits (which ARE agent `aw commit` commits) individually, finding no
trailers on any. E-01 now states the required property and requires re-derivation, with the numbers
kept as authoring context.

WHAT I DID NOT CHANGE. Route B, the env channel, and its two constants; the precedence order in E-03
(explicit trailers, then namespace, then env); the drop-and-warn treatment of a malformed value, which
matches `run_item_trailers`' documented rule that an absent value means unknown ownership and a
fabricated one is permanent; the decision not to refuse raw `git commit` (maintainer ruling, and the
reasoning is sound: a missing trailer reads as unknown, never as foreign); OQ-03's refusal to derive
`AW-Item` from the plan argument; and the `feature` classification with no release gate (verified:
neither this plan nor `j2srcc` carries `- Blocks-Release:`, and `evaluate_blocking_close` on the item
returns `legitimate=True` by the DE-GATED path).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1201 | HIGH | UNDER-SCOPE | E. Testing / G (an undeclared path a shipped assertion forces) | `tests/test_git_commit_helper.py::test_aw_commit_threads_trailers_and_lifecycle_delegates` asserts `work_cmd._trailers_from_args(argparse.Namespace()) == []`. Driven with `mock.patch.dict(os.environ, {"AW_RUN_ID": "run-20260926T010203Z-4242", "AW_ITEM_ID6": "abc123"})` and the prototyped fallback: returns two trailers. `grep -rln "_trailers_from_args" tests/` -> that file only. The file was absent from `- Scope-Paths:` | **A SHIPPED ASSERTION BREAKS UNDER THE ENV FALLBACK, AND F-5 NAMED THE WRONG TEST.** The cited byte-identity tests call `offer_commit` with an explicit `trailers=` and never reach the changed function, so the stated hazard was not the real one. The real one is the no-env default assertion, which the conftest scrub (E-06) is what protects. So E-06 and that test are coupled, the coupling was unstated, and the file was undeclared. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `tests/test_git_commit_helper.py` added to `- Scope-Paths:` and fenced to that one assertion, to be touched ONLY if the scrub proves insufficient. E-06 rewritten to name the real test and cite it in the comment it adds. V-06's reverted run must show that assertion failing. A second stop condition forbids weakening or deleting it. Added F-7. |
| PR-1202 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing (the plan's own contract unasserted) | Case (1) sets the env by hand (reader only); cases (5)/(6) assert on the captured env dict (writer only); E-03 defines a LOCAL run-id pattern rather than importing `runner_shared`, so `new_run_id`'s shape and the validator are two independent definitions | **NOTHING PROVED THAT WHAT THE WRITER EXPORTS IS A VALUE THE READER ACCEPTS, which is the entire contract.** Every case exercises one half. The risk is not theoretical: the plan deliberately keeps two separate definitions of the run-id format, and a divergence between them would silently stop every trailer from landing while all seven cases still passed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added E-08/V-08: capture the writer's exported `AW_RUN_ID` and feed THAT string through `_trailers_from_args`, for the plain and `-N`-suffixed shapes. V-08 requires stating that the value came from the captured env and was not re-typed, since a re-typed literal tests the reader twice and proves nothing. `Highest E allocated` 07 -> 08. |
| PR-1203 | MEDIUM | IN-SCOPE | E. Testing (a reused fixture whose value the change rejects) | `test_child_env_scrubs_driver_attest_for_both_hosts` uses `state = {"run_id": "run-test", ...}`, `item = {"id6": "abc123", ...}`. `run-test` does not match `^run-\d{8}T\d{6}Z-\d+(-\d+)?$`; all 283 real run dirs do; `abc123` matches `ID6_RE` | **THE REUSED HARNESS EXPORTS A RUN ID THE READER WILL DROP.** Since the write side does not validate, cases (5)/(6) pass asserting `AW_RUN_ID=run-test`, proving export but not usability. An executor who spots the mismatch may "fix" it by validating at the write side, which is the wrong half and would then break the reused harness. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now states the measurement, offers the two legitimate options (document the value, or use a valid one in your own copy of the state), and forbids adding write-side validation. V-04 requires stating which value case (5) asserts and whether the reader accepts it. Added F-8. |
| PR-1204 | MEDIUM | IN-SCOPE | C. Architecture (a deliberate asymmetry with no stated reason) | E-03 validates; E-04/E-05 as authored say only `child_env[RUN_ID_ENV] = str(state["run_id"])` with no statement either way | **VALIDATION IS AT THE READER ONLY, AND THE PLAN NEVER SAID WHY.** An unexplained asymmetry reads as an oversight, and the obvious "improvement" (validate at both ends) is wrong here: a runner that silently dropped its own malformed id would make a real run indistinguishable from no run, and would move the judgement out of the one place that warns. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 states the rule, the reason, and the measured consequence (a test-shaped id is exported then rejected); the gate carries a "WHERE VALIDATION LIVES" paragraph; V-04 requires the diff to show no write-side validation. Scope line now lists write-side validation as OUT. |
| PR-1205 | MEDIUM | IN-SCOPE | G. Plan executability (live-artifact counts stated as the bar) | Re-measured at review: 206 commits since 2026-09-22 with 1 trailered (plan says 188 with 1); 71 trailered across all refs (plan says 39). The 9 `work(...)` commits carry no trailers; the trailered set groups 77 under `closed by aw oc run` | **THE CONCERN AND F-1 PIN COUNTS OF A LIVE POPULATION, AND THEY HAVE ALREADY DRIFTED.** An executor re-running E-01 would find numbers matching neither, and could reasonably wonder whether the premise still holds. The PROPERTY is stable and is what the plan needs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states the required property, requires re-derivation, keeps the authoring numbers as context, and adds that a trailered `work(...)` commit in the corpus is NOT the stop condition (the scratch probe is). The Findings preamble records the drift and the stable shape. |
| PR-1206 | LOW | IN-SCOPE | A. Correctness (an artifact named by the wrong id, throughout) | `.aw/records/plans/pending/20260926-trailread-02-199u11-...ipd.md` carries `- Id: 199u11`, `- Order: 2`, `- From-Backlog: am1g38`; `.aw/records/backlog/graduated/...-am1g38-...backlog.md` carries `- Id: am1g38` | **THE PLAN CALLS THE ORDER 2 PLAN `am1g38`, WHICH IS ITS BACKLOG ITEM.** Stated that way in the Concern, Scope, Goal and Deferred, so a reader following it as a plan id finds no plan and may conclude the Order 2 work is unwritten when it exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal, Scope and Deferred now name plan `199u11` and note it graduated from `am1g38`. The `- Carrier: am1g38` field is deliberately LEFT pointing at the item (the carrier vocabulary resolves backlog and plans, and the item is the durable obligation). Added F-10. |
| PR-1207 | LOW | IN-SCOPE | A. Correctness (a stale status in the plan's own findings table) | `8apjpp` sits under `plans/executed/`; `runner_shared` already builds `[*_gch.run_item_trailers(run_id, id6), "AW-Committed-By: driver"]` for the review-lane commit; the plan's own Deferred entry cites it as executed evidence | **F-6 CALLS `8apjpp` "PENDING" WHILE THE DEFERRED SECTION CALLS IT EXECUTED.** The plan contradicts itself two sections apart, and the overlap it describes as prospective is already settled in the tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 corrected to record that `8apjpp` is executed and its trailers are live, citing the trailer list in `runner_shared` and the plan's location. |
| PR-1208 | LOW | IN-SCOPE | G. Plan executability (thin fence; an unstated security property) | Fence as authored: "the six paths in `- Scope-Paths:`" plus one expected-unmodified file; the gate said nothing about tamper resistance, while E-02 requires an honest-limit sentence in the code | **THE FENCE NAMED NO SURFACES, AND THE GATE OMITTED THE PROPERTY E-02 REQUIRES THE CODE ITSELF TO STATE.** A trailer looks like provenance; it is a consistency record a same-user process can forge, exactly as `AW_EXECUTION_ROLE` can be set. The code was told to say so and the approving human was not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence now names the in-scope surface per file plus three expected-unmodified surfaces (`runner_shared.pinned_child_env`, `run_item_trailers`' behavior, `tests/test_driver_attestation_gate.py`). The gate gains "THE HONEST SECURITY PROPERTY". The honesty rule names the two easiest-to-fake claims; a second stop condition is added; and the finalize instruction gains conditional runner/executor ownership plus the verified statement that no release gate is in play. |
| PR-1209 | LOW | IN-SCOPE | A. Correctness (a stale cross-reference in a file this plan edits) | `grep -rn "test_role_declaration_guard" --include=*.py .` -> two hits, both in `conftest.py`; `ls tests/ \| grep -i role` -> nothing | **`conftest.py` CITES A TEST FILE THAT DOES NOT EXIST**, twice, in the comment block E-06 extends. Pre-existing, unrelated to trailers, and not this plan's to repair. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded rather than repaired. Added F-12 with the measurement and a note telling the executor not to copy the pattern of citing a nonexistent test in the comment they add. Deliberately not repaired here: it predates this plan and fixing it would widen the diff in a file whose only intended change is a two-line scrub. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-1201: the env fallback breaks a shipped assertion. Declare the test file and allow the edit, or rely on the conftest scrub alone? | DECLARE THE FILE, fence it to that one assertion, and permit the edit ONLY if the scrub proves insufficient. | (a) Rely on the scrub and leave the file undeclared: rejected, because if the scrub turns out not to cover the case the executor has no declared path to fix it and will either edit an undeclared file or weaken the assertion under time pressure. (b) Declare it and just change the assertion: rejected, that would make the scrub untested and would remove the only shipped pin on the no-env default. (c) Change the assertion to a weaker form: rejected outright and forbidden in a stop condition, for the same reason. | The assertion read verbatim; the prototyped fallback's return value; `grep` showing that file is the only test reaching the function | yes |
| D-2 | PR-1202: should review add a test, or is the coverage gap acceptable for a `feature` plan? | ADD E-08, the writer-to-reader round trip. | (a) Accept the gap: rejected, the plan's whole deliverable is that two independently-defined formats agree, and nothing asserted it; a divergence would disable every trailer while all seven cases passed. (b) Make E-03 import `runner_shared` so there is one definition: rejected, that pulls a 32k-line runner module into every `aw commit`, which the plan explicitly and correctly avoided; a test is the right way to pin agreement between two deliberate definitions. | The case-by-case mapping of what each test touches; E-03's stated reason for the local constant | yes |
| D-3 | PR-1203/PR-1204: the harness's `run-test` is rejected by the reader. Fix the fixture, or validate at the write side? | NEITHER SILENTLY: state the asymmetry, keep validation at the reader, and let the executor choose to document the value or use a valid one. | (a) Validate at the write side too: rejected on a stated principle, a runner that drops its own malformed id makes a real run indistinguishable from no run and moves the judgement away from the one place that warns; it would also break the reused harness. (b) Mandate changing the harness value: rejected as unnecessary coupling to another test's fixture; either choice is defensible so long as it is stated. (c) Say nothing: rejected, the tests would then appear to prove end-to-end usability when they prove export. | `run-test` versus the pattern; 283 real run dirs matching; the harness state read verbatim | yes |
| D-4 | PR-1209: `conftest.py` cites a nonexistent test file. Fix it in this plan? | NO. Record it as INFO with the measurement. | (a) Fix it here: rejected, it predates this plan, has nothing to do with trailers, and would widen the diff in a file whose intended change is two lines; an unrelated repair inside a declared path is still scope creep. (b) File a backlog item: rejected, it is a comment typo with no behavioral consequence, so an item would record work nobody has decided to do; the note in the plan's Findings is proportionate. (c) Ignore it: rejected, the executor is about to write a comment in that exact block and should not copy the pattern. | The two `grep` results; the absence of any file by that name | yes |

### Deferred and open

- (none). All nine findings are FIXED in place; PR-1209 is fixed in the sense of being recorded with a
  measurement and an explicit decision not to repair it here (D-4), not silently dropped; it is filed at
  LOW rather than INFO because the typed vocabulary has no INFO tier. Two were HIGH
  and both were genuine execution hazards rather than polish: PR-1201 would have failed the suite via a
  shipped assertion in an undeclared file, and PR-1202 left the plan's own central contract unasserted.
  No finding was left OPEN or DEFERRED, so no escalation to a `- Blocking: yes` question is owed. All
  three pre-existing open questions were already resolved by the maintainer or the author; I re-read
  each and left all three resolutions standing, including OQ-02's risk-appetite ruling not to refuse raw
  `git commit`, whose reasoning I checked and agree with on the evidence (a missing trailer reads as
  unknown ownership, never as foreign, so a bypass costs attribution but cannot manufacture a false
  excuse).
