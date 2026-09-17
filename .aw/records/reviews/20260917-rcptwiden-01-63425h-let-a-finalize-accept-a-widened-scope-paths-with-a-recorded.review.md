# Review findings: plan 63425h

- Subject-Id: 63425h
- Subject-Type: ipd
- Reviewed-At: 2026-09-17
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `eabeaef8` in an isolated review lane. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0) before revision and `--phase review-finalize` CONFORMED after. No pre-review snapshot
was needed: the plan was committed and byte-identical to the lane input.

THE PLAN'S CENTRAL CLAIM IS TRUE, AND I REPRODUCED IT END TO END RATHER THAN READING IT. Two fixtures
built from the repository's own `tests/test_receipt_requirement_digest.py` plan text, driven through real
`LC.begin` / `LC.finalize_precheck` / `LC.finalize` against real git:

```text
CASE A-committed (same edits + HONEST declaration): 1 | the begin receipt for abc123 is STALE: the plan content changed since begin; re-run `aw ipd begin`.
CASE C-committed (edit undeclared, no widen, cohesive commit): 0
```

So declaring the path refuses and concealing it does not. The incentive gradient is real and the plan is
correct that it points at concealment.

I ALSO CONFIRMED THE THREE MEASURED INCIDENTS FROM GIT, which no prior artifact had done: reconstructing
each plan's pre- and post-widening text from its own commit (`i3d6ml`=`89324096`, `tx6q0h`=`e5fbe9c4`,
`sy7uwh`=`20311677`) and diffing the frozen region shows `must` and `validation` IDENTICAL in all three,
`scope` differing in all three, removals NONE in all three, and the added entries exactly the five files
F3 names. F3 is accurate.

FOUR FINDINGS CHANGE WHAT THE PLAN MUST BUILD, and three of them would have shipped a fix that did not
work. They are the reason this review took the time it did.

FIRST, F-6 IS FALSE AND ITS FALSITY IS GOOD NEWS. The plan warns that the receipt stores only the digest,
so a structural comparison cannot decompose the receipt side, and instructs the executor to either find a
reconstruction or "state honestly that a v2 receipt cannot be decomposed". The receipt stores `scope_paths`
VERBATIM (`ipd_lifecycle.py:1095`) and `finalize_precheck` already reads it (`:1630`). I generated a real
receipt to be sure; its keys include `scope_paths: ['agent_workflows/demo.py', 'tests/test_demo.py']`. That
makes a SUBSTITUTION TEST available with no schema change: put the receipt's stored scope back into the
current plan's payload, re-hash, compare. Verified on all three incidents (reproduces the stored digest:
True, True, True) with a negative control that also rewrites an E-item action (False, False, False). An
executor taking the plan's escape hatch would have built a v3 receipt for nothing.

SECOND, THE `--scope-reason` REQUIREMENT WOULD HAVE BEEN VACUOUS. `finalize_precheck` computes
`out_of_scope` against the RECEIPT's `scope_paths`, so a newly added path is judged against the OLD fence.
Measured with the staleness predicate stubbed out, an UNCOMMITTED edit to a widened path yields
`out_of_scope_paths: []` and `disregarded_unowned_paths: ['tests/test_extra.py']`, so `_reconcile_scope`
demands nothing at all. The plan's OQ-01 says "if unanswered, the strict form ships"; as authored, the
lenient form would have shipped while the plan claimed otherwise. E-04 now carries an explicit
unconditional per-added-path demand, and V-04 requires the uncommitted variant specifically, because that
is where a vacuous pass hides.

THIRD, AND MOST IMPORTANT, THE FIX AS AUTHORED WOULD NOT HAVE SAVED THE THREE LANES IT CITES. All three
were finalized BY THE RUNNER. `runner_shared.compute_scope_reconciliation:8562-8596` builds its reason map
solely from `audit["out_of_scope_paths"]`, and `oc_runipd.driver_finalize:1304-1328` passes only what that
map contains, so for an uncommitted widened path the runner supplies no `--scope-reason`. Net effect of
E-04 alone: a STALE refusal becomes a MISSING-REASON refusal, and the same three lanes strand for a new
reason. `runner_shared.py` is now in the fence for exactly this, E-04 owns the runner half, and E-07 must
prove the fix end to end THROUGH the runner rather than by asserting the predicate accepts.

FOURTH, A STRICT SUPERSET CAN NEUTER THE WHOLE FENCE. Driving `_scope_match` over candidate additions:
`tests/` is a strict superset that admits every file under `tests/`; `agent_workflows` admits the package
(a bare directory matches by PREFIX at `:1504-1505`, with no glob character to notice); `*` admits
`tests/test_secret.py`, `agent_workflows/check_engine.py`, `RELEASING.md` and `.aw/records/specs/x.spec.md`
simultaneously. One added entry plus one boilerplate reason converts a four-file fence into a repo-wide
one, after which nothing is out of scope and nothing demands anything. That is strictly worse than the bug,
since today the refusal at least stops. New E-08 restricts eligibility to LITERAL FILE PATHS and reuses
`_scope_match`'s own classification so the two cannot disagree.

TWO SMALLER GAPS. The plan's own `Scope-Paths` omitted `tests/test_receipt_requirement_digest.py`, which is
where every existing assertion about `frozen_region_digest`, the v2 binding and the v1 fallback lives, i.e.
precisely where the new tests belong; filed with deliberate irony as F-13 and added. And a widening
SILENCES `check.scope-drift` for the added path, because the advisory reads the PLAN's current scope
(`check_engine.py:1366`) rather than the receipt's; that may be correct but the plan never said so, and
`wmnmei` owns the advisory, so E-02 must report the interaction without editing it.

WHAT I FIXED. Corrected the Concern's second half with the measured disregarded-unowned behavior; added the
substitution test to the Goal with its verification; withdrew F-6 in place with the receipt keys as
evidence; rewrote E-02 with the six consumers I located and the `check.scope-drift` question; rewrote E-03
to implement the substitution test and to share ONE payload builder with `frozen_region_digest`; rewrote
E-04 with the unconditional reason demand, the no-double-demand requirement and the runner half; added
E-08 (fence-neutering) and E-09 (three ineligible receipt shapes); added set-comparison and reordering to
E-05; rewrote E-06 with the measured test exposure and the spec-eligibility requirement; rewrote E-07 to
demand an end-to-end reconstruction through the runner; added F-8 through F-13; raised OQ-02 for the
directory/glob policy; added the worker-role test-environment note; expanded the fence by three files; and
tightened the execution contract with the four measured facts an executor must not re-derive from the old
text. `Highest E allocated` raised 07 -> 09.

WHAT I DID NOT DO. I did not implement the fix, and I did not decide either open question's policy: both are
non-blocking, both ship in the fail-closed direction, and both are the maintainer's to relax.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | C. architecture; E. testing (the fix does not reach its own incident) | `runner_shared.py:8562-8596`; `oc_runipd.py:1304-1328`; measured `out_of_scope_paths: []` for an uncommitted widened path | **THE FIX WOULD NOT HAVE SAVED THE THREE LANES IT CITES.** All three incidents were finalized by the runner, whose auto-reconciliation derives its reason map only from `out_of_scope_paths`, which does not contain an uncommitted widened path. E-04 alone converts a STALE refusal into a MISSING-REASON refusal and strands the same lanes. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added as F-10. E-04 now owns the runner half (surface the added set in precheck evidence, teach `compute_scope_reconciliation` to auto-reason it); `agent_workflows/runner_shared.py` and `tests/test_rununify_host_descriptor.py` added to the fence; E-07 rewritten to require an end-to-end reconstruction THROUGH the runner; Required tests item 7 added; V-07 rewritten to reject a predicate-only check. |
| PR-002 | BLOCKER | IN-SCOPE | A. correctness (the plan would ship the opposite of what it claims) | `finalize_precheck:1630` judges against the receipt's scope; measured `disregarded_unowned_paths: ['tests/test_extra.py']`, `out_of_scope_paths: []` | **THE `--scope-reason` REQUIREMENT WOULD HAVE BEEN VACUOUS, so OQ-01's "the strict form ships" was false.** Reusing the existing surface without an added demand yields NO reason requirement for an uncommitted widened path, because that path is disregarded as unowned rather than reported out-of-scope. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | Added as F-9. E-04 now requires a reason for EVERY member of `added` unconditionally, and separately requires that one reason satisfy both demands in the committed case without double-recording. V-04 demands BOTH variants and says a committed-only paste does not satisfy it. OQ-01 amended to record that the strict form was not what the old text implemented. |
| PR-003 | HIGH | IN-SCOPE | B. security-adjacent (authorization scope); C. architecture | `_scope_match:1475-1505` driven over `tests/`, `agent_workflows`, `agent_workflows/**`, `*` | **A STRICT SUPERSET CAN NEUTER THE WHOLE FENCE.** One added directory or glob entry, with one reason string, converts a four-file fence into a repo-wide one, after which no edit is out of scope and none demands justification. Strictly worse than the bug being fixed, since the current refusal at least stops. The accept condition as authored did not exclude it. | C:Low; U:Medium; S:Medium; F:Medium; Overall:Medium | FIXED | Added as F-11 and new E-08: only a LITERAL FILE PATH is eligible; a directory or glob addition refuses with the entry named. Eligibility reuses `_scope_match`'s own branch classification (including the bare-directory prefix case) with a shared-table test so the two cannot disagree. V-08 added; Required tests item 6 added; OQ-02 raised for the policy. |
| PR-004 | HIGH | IN-SCOPE | A. correctness (a false premise that misdirects the executor) | receipt generated at review, keys include `scope_paths`; `ipd_lifecycle.py:1095`, `:1630`; substitution verified on all three incidents | **F-6 IS FALSE AND ITS ESCAPE HATCH WOULD HAVE CAUSED REAL WORK.** The receipt does store `scope_paths` verbatim and finalize already reads it, so the receipt side needs no reconstruction and no v3 schema. An executor taking the plan's "state honestly that a v2 receipt cannot be decomposed" path would have invented a field for nothing. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-6 WITHDRAWN in place with the receipt keys pasted as evidence rather than deleted, so the reasoning stays auditable. The substitution test is stated explicitly in the Goal with its verification (reproduces for all three incidents; negative control does not). E-03 rewritten to implement it and forbidden from bumping the schema. V-03 rewritten accordingly. |
| PR-005 | HIGH | IN-SCOPE | A. correctness (the Concern understates its own case) | two end-to-end fixtures: uncommitted -> disregarded, committed-cohesive -> reason demanded | **THE ASYMMETRY IS WIDER THAN THE CONCERN STATED.** "The undeclared edit finalizes fine with `--scope-reason`" is true only for the committed-cohesive case. An uncommitted undeclared edit is DISREGARDED ENTIRELY and demands nothing, so concealment is not merely cheaper than honesty, it is free in the common case. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-8; the Concern corrected in place with both measurements; V-01 now requires BOTH concealment variants pasted with a statement of which demanded a reason. The gap itself is explicitly DEFERRED with a reason (closing it needs the shared-checkout analysis `_working_tree_path_is_owned`'s docstring describes) rather than absorbed. |
| PR-006 | HIGH | UNDER-SCOPE | E. testing (the owning test file was undeclared) | `tests/test_receipt_requirement_digest.py:99-249`; `rg -l frozen_region_digest tests/` | **THE FILE THAT OWNS THIS BEHAVIOR WAS NOT IN `Scope-Paths`.** `FrozenRegionDigestTests` and `ReceiptBindingTests` hold every existing assertion about the digest, the v2 binding and the v1 fallback, which is where E-03's and E-09's tests belong. The plan declared two other lifecycle test files instead. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F-13 (filed with the irony noted, since this plan exists because an undeclared test file strands a lane) and added to the fence, along with `tests/test_rununify_host_descriptor.py` for the runner half. |
| PR-007 | MEDIUM | UNDER-SCOPE | D. domain invariants (an unreasoned-about input shape) | `_frozen_scope_paths` vs `_requirements_from_plan` measured on a grandfathered plan; `:860-864` | **THREE RECEIPT/PLAN SHAPES WERE NEVER REASONED ABOUT.** A grandfathered plan has `scope_paths == []` while `requirements["scope"] == ["grandfathered", <prose>]`, so a substitution that replaces only one of the two mis-compares; a plan that BECOMES grandfathered empties the allowlist and must read as a REMOVAL, not an unchanged empty set; and a legacy v1 receipt must not be judged by a rule it was never bound under. The plan mentioned only the v1 case, in a convention bullet, with no E- or V-item. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added new E-09 pinning all three as INELIGIBLE, each with its own test and its reason in the docstring, plus an assertion that the v1 path never invokes the new comparison. V-09 added; Required tests item 5 broadened from the v1 case to all three; the field distinction added to Project conventions. |
| PR-008 | MEDIUM | UNDER-SCOPE | C. architecture (a silent-drift hazard on a gate input) | `frozen_region_digest:505-513` builds the payload as an inline literal | A second hand-written copy of the `{"scope_paths": ..., "requirements": ...}` payload literal in the new comparison would drift from the original, and a drifted copy fails SILENTLY in the dangerous direction: the substitution never matches, the accept never fires, and the symptom is indistinguishable from the bug being fixed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires ONE shared payload builder called by both functions, and V-03 requires a test that would FAIL if a second copy were introduced rather than a statement that they agree. |
| PR-009 | MEDIUM | UNDER-SCOPE | C. architecture (an undocumented interaction with another plan's surface) | `check_engine.py:1366` reads `_frozen_scope_paths(text)` from the plan, not the receipt | **A WIDENING SILENCES `check.scope-drift` FOR THE ADDED PATH,** the moment it is declared and before any finalize accepts anything. Arguably correct, but it means the honest declaration is also the way to silence the advisory, and this is the plan that makes declaring safe. Unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-12; E-02 must state the interaction explicitly and V-02 requires the answer. Confined to REPORTING: `wmnmei` owns the advisory and the deferral section now says so, so this plan does not edit `check_engine.py`. |
| PR-010 | MEDIUM | UNDER-SCOPE | E. testing (a false baseline would be recorded) | `env -u AW_EXECUTION_ROLE python3 -m pytest` -> `91 passed`; with the variable -> `2 failed` | The plan requires a bare suite run against a baseline, but in a managed worker lane `AW_EXECUTION_ROLE=worker` makes `run_begin`/`run_finalize` refuse (`AW-LIFECYCLE-ROLE-001`) and two `test_ipd_lifecycle_cli.py` CLI tests fail. An executor would either record a false baseline or "fix" tests that are not broken. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests item 1 now names both tests, the cause, the `env -u` form and its `91 passed` result, and instructs the executor to say which form was run and not to edit the tests. Added to Project conventions with the two refusal sites. |
| PR-011 | LOW | IN-SCOPE | A. correctness (an ordering artifact could read as a contract change) | `Scope-Paths` is parsed to a LIST (`ipd_schema.parse_scope_paths:555`) | A reordering of the same `Scope-Paths` entries is semantically identical but would read as a removal plus an addition under a naive list comparison, refusing a plan that changed nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires SET comparison of entry strings, stated in code, and V-05 requires a pure-reordering case asserted unchanged. |
| PR-012 | LOW | UNDER-SCOPE | G. spec effects (an amendment broader than the code) | spec `:1009`; `zzcrlo`'s execution contract forbidding its own executor from editing this spec | The spec amendment as scoped would authorize "an additive scope widening with a recorded reason" without the eligibility conditions, which is broader than what E-08 and E-09 permit in code, leaving the spec authorizing the whole-repo fence the code refuses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 must write the literal-file-path restriction and the three ineligible shapes INTO the clause; the spec-sync section states the amendment-authority position (`zzcrlo` forbids its own executor from touching this spec, so there is no competing claim) and names the three spec-reading test files with the measured finding that none reads Section 5.5. V-06 requires the spec diff pasted to prove no other section moved. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-6 says a v2 receipt cannot be decomposed. Accept it and let the executor find a route, or resolve it? | RESOLVE IT. The receipt stores `scope_paths` verbatim, so the substitution test works today; I wrote it into the Goal with its verification and forbade a schema bump. | (a) Leave F-6 and let E-03 decide, rejected: the plan's own escape-hatch wording ("state honestly that a v2 receipt cannot be decomposed and state what E-04 therefore needs") invites inventing a receipt field, which is a schema change to a gate input made on a false premise. (b) Delete F-6, rejected: withdrawing it in place with the evidence keeps the reasoning auditable and stops it being re-derived. | `ipd_lifecycle.py:1095` writes `scope_paths`, `:1630` reads it; a receipt generated at review carries the key; substitution reproduces the stored digest for `i3d6ml`/`tx6q0h`/`sy7uwh` and fails on an E-text negative control | yes |
| D-2 | The runner cannot supply a reason for a widened path. Widen this plan's fence to `runner_shared.py`, or file it as a follow-up? | WIDEN THIS PLAN. Without it the fix does not reach the incident the plan is entirely justified by. | (a) File a follow-up plan, rejected: the plan's `Blocks-Release: next` and its whole cost argument rest on the three measured lanes, so shipping a version that leaves them stranded for a NEW reason would make the release gate claim false. (b) Note it as a finding without changing scope, rejected: E-07 would then "pass" on a predicate check while the runner still refused, which is precisely the vacuous-verification failure this review found twice elsewhere. | `runner_shared.py:8562-8596` derives reasons only from `out_of_scope_paths`; `oc_runipd.py:1304-1328` passes only that map; the three incidents were runner-finalized | yes |
| D-3 | Is a strict superset a sufficient accept condition? | NO. Restrict eligibility to LITERAL FILE PATHS and refuse a directory or glob addition (new E-08), and raise the policy as OQ-02 rather than settling it. | (a) Accept any strict superset, rejected outright: measured, one `*` entry admits the whole repository, which is a worse failure than the bug and would be granted by an execution to itself. (b) Allow a directory but demand a reason per directory, rejected: the reason is auto-generated boilerplate on the runner path (see OQ-01's cost note), so it would be no control at all. (c) Decide the policy myself, rejected: how much fence an execution may grant itself is a gate policy question, so the code ships fail-closed and the maintainer may relax it. | `_scope_match:1475-1505` driven over five entry shapes; the bare-directory prefix branch at `:1504-1505` | yes |
| D-4 | Should this plan also close the disregarded-unowned hole F-8 found? | NO. Defer it with a stated reason and keep this plan to making honesty work. | (a) Close it here, rejected: `_working_tree_path_is_owned`'s docstring records that disregarding an unattributable dirty path is a deliberate shared-checkout concession, since demanding a reason for a co-worker's file forces a false claim into a permanent record; reversing that needs its own analysis of the concurrent-agent case. (b) Say nothing about it, rejected: it is the other half of the asymmetry the plan describes and omitting it would misrepresent what the fix achieves. | `_working_tree_path_is_owned` docstring and the `mm6wuz` measurement it cites (10 demanded reasons, 8 of them other agents' commits) | yes |
| D-5 | Two lifecycle CLI tests fail in this environment. Report a broken suite, or diagnose? | DIAGNOSE. `AW_EXECUTION_ROLE=worker` makes `run_begin` refuse by design; `env -u` gives `91 passed`. Recorded as a note for the executor. | (a) Report `2 failed` as a repository defect, rejected: it would send an executor to "fix" a working role gate. (b) Say nothing, rejected: the plan requires a baseline suite run, and an executor in a worker lane would record a false one. | `AW-LIFECYCLE-ROLE-001` refusals at `ipd_lifecycle.py:3686` and `:3866`; both runs pasted at review | yes |
| D-6 | Verdict, given two BLOCKER-severity findings? | APPROVE WITH REVISIONS APPLIED, readiness GO - PENDING HUMAN APPROVAL. Both blockers were FIXED by in-place revision, and the two open questions are non-blocking with the fail-closed form shipping. | (a) `REVIEWED - OPEN QUESTIONS` / NO-GO, rejected: no finding is left OPEN or DEFERRED at or above the gate threshold, and the workflow reserves NO-GO for a genuine not-ready condition rather than for a plan whose findings were repaired. (b) `REJECT - NEEDS REPLAN`, rejected: the approach is sound, the premise reproduces, and every defect was a bounded edit; the fix shape (narrow the predicate, do not remove it) is the one the repository already used for this bug class. | workflow readiness table; all twelve findings carry `FIXED`; `aw ipd lint --phase review-finalize` conforming | yes |

### Escalation of the irreversible decisions

None of this round's six decisions is judged `Reversible: no`. Every one is undone by editing this plan
before it executes: nothing here publishes an interface, migrates data, deletes anything, or produces a
released artifact. Stated explicitly rather than left blank, because two of them LOOK irreversible and are
not. D-2 widens a scope fence, which sounds like a contract change, but the plan is `to-review`/`reviewed`
and unexecuted, so the fence is still a proposal. D-3 shapes a GATE, which would be irreversible once
shipped, and that is exactly why the decision I made was to ship the FAIL-CLOSED form and escalate the
policy as OQ-02: refusing a directory addition can be relaxed later without breaking anyone, while
permitting one and later revoking it would be a regression for whoever relied on it. The irreversible act
is deliberately not authorized by me.

### Honest limits of this review

- I DID NOT IMPLEMENT THE FIX. Every measurement is against unmodified HEAD `eabeaef8`, with one
  exception noted below. The substitution test is verified as a PREDICATE over real plan texts, not as
  shipped code inside `receipt_is_current`.
- ONE MEASUREMENT REQUIRED STUBBING. To see what the reconciliation would demand for a widened path I
  monkeypatched `LC.receipt_is_current` to return True in a throwaway process, because the staleness
  refusal fires first. That is how F-9 and F-10 were measured. The stub was in-process and temporary; no
  repository file was changed. An executor should reproduce the same facts against the REAL predicate once
  E-03 lands, which is what V-04 demands.
- MY RUNNER FINDING IS A SOURCE READ, NOT A DRIVEN RUN. I did not execute `aw oc run`. F-10 rests on
  reading `compute_scope_reconciliation` and `driver_finalize` and on the measured `out_of_scope_paths`
  contents that feed them. E-07 is written to require the driven proof rather than to inherit my inference.
- I DID NOT RUN THE FULL SUITE. I ran `tests/test_receipt_requirement_digest.py`,
  `tests/test_ipd_lifecycle_cli.py` and `tests/test_finalize_isolated_commit.py`: `91 passed` with
  `AW_EXECUTION_ROLE` unset, `2 failed, 89 passed` with it set. The plan's overall suite baseline is
  unverified by me.
- MY CONSUMER LIST COMES FROM A NAME SEARCH across `agent_workflows/` and `tests/`. A consumer reaching the
  digest by another route (a fixture reading a receipt file, a helper passed the function) would not have
  appeared, which is why E-02 must re-derive it rather than inherit my table.
- I DID NOT VERIFY THE RUN-LEVEL COST FIGURES in F2 ($95.71 of $212.60, the timings, the cascade to
  `5e4sb6`/`dhuape`/`alw22r`). The run directory for `run-20260917T023628Z-4108757` is not present in this
  lane; only the backlog item `3dg3dv` and this plan reference the run id. I verified the SHAPE of the
  incident from git instead, which is the part the fix depends on. The dollar figures remain the author's.
- I DID NOT DECIDE EITHER OPEN QUESTION'S POLICY. OQ-01 (reason per added path) and OQ-02
  (directory/glob eligibility) both ship in the strict direction and both are the maintainer's to relax.
