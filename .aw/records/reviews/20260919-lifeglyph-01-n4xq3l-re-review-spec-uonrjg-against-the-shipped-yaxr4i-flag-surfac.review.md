# Review findings: plan n4xq3l

- Subject-Id: n4xq3l
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `6ce719d5`. The plan on disk was byte-identical to the sealed lane input
(`sha256 a794daec...`, confirmed by `diff`), and `git status --porcelain` was empty, so no pre-review
snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported `clean`, 0
findings, exit 0; the same at `--phase review-finalize` after the revisions.

THE PLAN'S PURPOSE IS CORRECT AND ITS EVIDENCE IS SOUND. Spec `uonrjg` Section 12a really does impose a
re-review gate on its own implementation, the reason really is mechanical (`yaxr4i` moves the flag
surface A11 to A13 are written against), and a dedicated child for a documentary gate is the right
shape. Every upstream claim I checked held: `yaxr4i` is `- Status: approved` and still in `pending/`, so
the dependency edge is live rather than already-satisfied; and F-03's warning is true at HEAD, with the
retracted non-TTY promise intact at `docs/cli-output-contract.md:159-163` under a heading that still
calls it a Hard Cutover.

WHERE THIS REVIEW SPENT ITS EFFORT: the plan's single executable instruction names a workflow that
cannot do the job and would damage the spec if run. That is one root cause with two distinct harms, so
it is recorded as two findings sharing a fix.

**1. `/spec-review` refuses the spec's actual status, so E-01 would have discharged nothing.** The
workflow's Step 0.1 is explicit:

```text
spec-review.md:111-114
  A spec at `approved`, `implementing`, `implemented`, `deferred`, `parked`, or `superseded` is
  NOT REVIEWED with that status as the reason. Re-reviewing a spec already at `reviewed` is
  legitimate ONLY when explicitly requested.
```

`uonrjg` is `- Status: approved` (line 4). So a conforming run classifies it NOT REVIEWED, produces no
round, and this plan's entire reason for existing fails silently while every checklist item can still be
ticked. The plan half-anticipated this: its Step 0 note quotes Section 12a's "a re-review appends a new
round and keeps the status `reviewed`", which assumes a spec at `reviewed`. That sentence was written in
the same 2026-09-13 round that approved the spec, which is how the premise went stale immediately.

**2. Running it anyway would de-approve a release-gating spec and arm a gate against its
re-approval.** Two independent harms, both measured:

```text
attention_contract.transition_allowed('approved','reviewed')  -> True
```

So `spec-review.md`'s own transition step (`aw specs set reviewed <id6>`) is not refused by the
transition table; it succeeds, dropping `uonrjg` from `approved` to `reviewed` and requiring a fresh
`--by-human` approval that AGENTS.md reserves to the maintainer. Separately, that workflow writes a
typed `.review.md`, and its own text states what that does:

```text
spec-review.md:276-281
  Filing a spec review record ARMS A LIVE GATE on that spec's approval. `aw specs set approved`
  consults `plan_readiness.approval_refusals`, which consults `review_findings.subject_gating_blocks`
  keyed on the artifact's `- Id:` bullet, and specs carry one. So an unfixed finding at or above the
  threshold, or a record that fails to PARSE, will REFUSE that spec's approval, and that refusal has
  NO override by design.
```

`uonrjg` carries `- Blocks-Release: next`, so the combined failure mode is: a documentary check
de-approves the spec that gates the release, then blocks its re-approval on any finding the round
happened to leave open. The fix keeps the intent and drops the machinery: E-01 now performs the re-read
directly and records it with `aw specs note`, which appends history "WITHOUT changing its status" (its
own `--help`) and works at any status. Three writes are now forbidden by name, and V-01 demands negative
proof of each.

**3. The waived suite run is not safely waivable.** The plan reasoned "no code changes, so no suite run
is required". But 25 test modules read the LIVE repository tree rather than a fixture
(`grep -rlc "parents\[1\]" tests/*.py` -> 25), and this child edits a tracked record in that tree. I ran
the bare suite in this lane to give the executor a baseline it can diff against:

```text
8369 passed, 3 skipped, 2 xfailed in 100.98s (0:01:40)
```

Required tests now carries that baseline with an instruction to compare NODE IDS rather than totals
(the plan corpus is mutable, so the count moves), plus `aw check specs`, which is the cheap check that
actually covers this child's deliverable. I checked the one live-repo spec-handoff test
(`test_check_engine_spec_handoff.py:216`) and it pins `c4gd2h`, not `uonrjg`, so it is not a live
hazard; the point stands for the corpus-wide record checks.

**4. The gate lacked a scope fence and the honesty rule.** Added both, with the fence naming the three
forbidden writes as a distinct category from ordinary out-of-scope edits (each forges a signal or moves a
release gate rather than merely exceeding declared paths), and with the out-of-scope case routed to the
justify-at-finalize path rather than a stop directive. One genuine stop condition IS retained per the
2026-09-01 ruling's carve-out: if `yaxr4i` landed but the contract doc still carries the retracted
promise, A11's premise is absent and re-deriving it from code is something the spec explicitly forbids.

**5. Two smaller corrections.** The Spec-sync section called the deliverable "a spec amendment"
unconditionally, when the guaranteed write is only a history round and the amendment is conditional on
E-02 finding divergence; overstating it invites an executor to amend something to have done the work.
And the lifecycle line prescribed a hand-rolled `git mv` beside `aw ipd finalize`, which the plan-review
contract flags; it now states the conditional runner/executor ownership instead.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | BLOCKER | IN-SCOPE | G. executability; A. correctness | `.aw/system/workflows/spec-review/spec-review.md:111-114`; `uonrjg` line 4 `- Status: approved` | E-01 instructed running `/spec-review` on `uonrjg`, but that workflow classifies an `approved` spec as NOT REVIEWED and admits a re-review only at `reviewed`. The Section 12a gate this plan exists to discharge would have discharged NOTHING while every checklist item could still be ticked | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-01 rewritten to perform the re-read directly and record it via `aw specs note`, with the refusal quoted and the reason attached; `Scope` and the Proposed-changes list updated to match |
| PR-102 | HIGH | IN-SCOPE | B. security/authority; A. correctness | `attention_contract.transition_allowed('approved','reviewed')` -> True; `spec-review.md:259-284`; `uonrjg` `- Blocks-Release: next` | Running that workflow anyway would (a) de-approve a release-gating spec via its `aw specs set reviewed` step, which the transition table permits, forcing a fresh `--by-human` approval reserved to the maintainer, and (b) file a review record that arms an approval gate whose refusal has NO override, blocking re-approval | C:Low; U:Low; S:Medium; F:Medium-High; Overall:Medium | FIXED | Three writes forbidden by name in E-01, Scope, Spec-sync and the gate (`- Status:`, `- Readiness:`, a `.review.md` for this spec); V-01 now demands negative proof of all three |
| PR-103 | MEDIUM | UNDER-SCOPE | E. testing and verification | `grep -rlc "parents\[1\]" tests/*.py` -> 25 live-repo test modules; measured baseline `8369 passed, 3 skipped, 2 xfailed` at `6ce719d5` | "No code changes, so no suite run is required" is unsafe: 25 test modules read the live repository tree and this child edits a tracked record in it, so a validation gap existed with no way to distinguish a caused failure from a pre-existing one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bare suite run and `aw check specs` now required, with the measured baseline recorded and a compare-node-ids-not-totals rule; V-03 demands both |
| PR-104 | MEDIUM | IN-SCOPE | G. executability; honest documentation | plan Spec-sync section; `aw specs note --help`; Section 12a's `reviewed` premise | Two stale claims: the deliverable was called "a spec amendment" unconditionally when the guaranteed write is only a history round, and the Step 0 note cited a Section 12a sentence whose premise (`reviewed`) does not hold for this spec, which is what licensed the wrong mechanism | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync now separates the guaranteed write from the conditional amendment and names the forbidden writes; Step 0 records the corrected premise and that `approved -> reviewed` is legal, so the guardrail is the instruction |
| PR-105 | LOW | UNDER-SCOPE | G. executability; execution contract | plan gate (original final paragraph); no scope fence, no honesty rule, hand-rolled `git mv` beside `aw ipd finalize` | The gate lacked a scope fence, lacked the paste-the-actual-output honesty rule, did not state OQ-01's conditional disposition, and prescribed a hand-rolled `git mv` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries the fence (with the forbidden-write category and the justify-at-finalize path), the honesty MUST, OQ-01's disposition, one legitimate stop condition, and conditional runner/executor finalize ownership |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01 names a workflow that refuses this spec's status. Escalate as blocking, or re-specify the mechanism in place? | RE-SPECIFY in place: perform the re-read directly and record it with `aw specs note`, forbidding `/spec-review`, any `aw specs set` on this spec, and any `.review.md` for it. Not escalated. | (a) Escalate `Blocking: yes`: rejected, this is answerable from repository evidence (the workflow's own Step 0.1, the transition table, and the `note` verb's documented contract) rather than from maintainer preference, so escalating would spend a human turn on a settled question. (b) Change the spec to `reviewed` first so `/spec-review` accepts it: rejected as actively harmful, since it de-approves a release-gating spec to satisfy a tool precondition and needs a `--by-human` re-approval. (c) Amend Section 12a's wording as part of this plan: rejected, the sentence's conclusion is right and only its premise is stale; rewriting an approved spec's prose to fix a plan is the wrong direction, and the plan can simply use the correct verb. | `spec-review.md:111-114` (refuses `approved`); `uonrjg` line 4 `- Status: approved`; `attention_contract.transition_allowed('approved','reviewed')` True; `spec-review.md:259-284` (its setter step and the approval-gate arming); `aw specs note --help` ("WITHOUT changing its status"). | yes |
| D-2 | The plan waives the suite run. Accept the waiver for a docs-only child, or require a run? | REQUIRE a bare run plus `aw check specs`, and RECORD a measured baseline so a pre-existing failure is distinguishable. | (a) Accept the waiver: rejected, 25 test modules read the live tree and this child writes a tracked record in it, so "no code changes" does not imply "no test can break". (b) Require only `aw check specs`: rejected as the cheaper half of the right answer; it covers the record's conformance but not the corpus-reading tests. (c) Name specific test modules to run: rejected, a narrowed run needs `-o addopts=""` to report counts and the repo contract prefers the bare suite; naming modules also dates as tests move. | `grep -rlc "parents\[1\]" tests/*.py` -> 25; `tests/test_check_engine_spec_handoff.py:216` is live-repo but pinned to `c4gd2h`, not `uonrjg`; bare run in this lane at `6ce719d5` -> `8369 passed, 3 skipped, 2 xfailed in 100.98s`. | yes |
| D-3 | OQ-01 asks whether amending a criterion needs fresh maintainer approval. Resolve it, or leave it open? | LEAVE OPEN, non-blocking, and sharpen its rationale rather than answering it. | (a) Resolve it as "no approval needed": rejected, `uonrjg` carries `Blocks-Release: next`, so moving its acceptance bar moves a release gate, and AGENTS.md reserves approval authority to the human; an agent answering this would be authorizing its own future latitude. (b) Make it `Blocking: yes`: rejected, it is CONDITIONAL on E-03 finding a divergence, and the common case (no divergence, history append only) is provably approval-free because `aw specs note` changes no status and no requirement, so blocking the plan on it would stall a gate that may never fire. | `aw specs note --help` (no status change); `uonrjg` `- Blocks-Release: next`; AGENTS.md's approval-attestation rule and the `--by-human` floor in `TRANSITION_AUTHORITY['->approved']` (`{'who': 'human', 'by_human': True, ...}`). Judged REVERSIBLE because the decision only defers the question, and the harm path it leaves open is now closed IN THE PLAN: E-03/OQ-01 require the executor to surface an amended criterion to the maintainer, and the gate forbids any `aw specs set` on this spec and any self-written `--by-human`. Without those mitigations this row would be irreversible and would need escalation. | yes |
