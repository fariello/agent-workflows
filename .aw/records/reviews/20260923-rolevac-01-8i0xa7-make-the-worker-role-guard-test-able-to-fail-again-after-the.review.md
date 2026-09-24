# Review findings: plan 8i0xa7

- Subject-Id: 8i0xa7
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `166bf49b` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review; `--phase review-finalize` conforms after
revision. Nothing below is structural.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
entirely on RUNNING the claims. Doing so found TWO BLOCKERS: an edit an executed plan forbids and that
would silently disable a second guard, and a live 42-test regression that falsifies the plan's premise.

### What re-measured TRUE

```text
# F-2: the scrub works; the marking no longer changes the result
python3 -m pytest tests/test_ipd_lifecycle_cli.py                      -> 89 passed
AW_EXECUTION_ROLE=worker python3 -m pytest tests/test_ipd_lifecycle_cli.py -> 89 passed

# F-3: the runners still export it; runner_shared scrubs it nowhere
oc_runipd.py:3487   child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER
agy_runipd.py:2482  child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER
grep AW_EXECUTION_ROLE|EXECUTION_ROLE_ENV agent_workflows/runner_shared.py -> one COMMENT only
```

### The headline claim was too strong (F-6)

The plan says the guard "can no longer fail for ANY ambient value". Measured on the same node id:

```text
WITH re-assert plugin    exit=1  1 failed in 0.30s
WITHOUT plugin           exit=0  1 passed in 0.28s
```

The marked condition IS observable through a `-p` plugin whose `pytest_configure` runs after conftest's
import-time pop and before collection. So the real defect is that the ORDINARY route (an exported
variable) is dead, which is still worth fixing, but it does not license removing the test.

### BLOCKER 1: E-02 instructs a forbidden edit that would disable a second guard (F-7)

EXECUTED plan `8b9ufm` (`- Blocks-Release: next`) declares `tests/test_worker_role_refusal.py` and says:

> A WORKER LANE REDS ONE TEST BY CONSTRUCTION. ... Do not "fix" it and do not let new assertions depend
> on ambient env.

and again, in its validation section, "name it, say so, and do not modify it." Its F-18 is a CONSTRAINT
ON NEW ASSERTIONS, not a design for changing this one. `6z5yos` misread it ("approved plan 8b9ufm ... its
F-18 is precisely this") and the plan inherited the misreading. `8b9ufm`'s own executed record even
states the executor "did not modify `test_driver_own_process_is_not_worker_role` either".

The decisive fact is independent of that prohibition:

```text
tests/test_role_declaration_guard.py
  _KNOWN_AMBIENT_ASSERTING = "tests/test_worker_role_refusal.py"
  # Deliberately NOT protected: this test asserts about the AMBIENT environment by design, so it is
  # role-dependent on purpose. APPROVED plan `8b9ufm` owns the file and explicitly forbids "fixing" it.

class TheReassertProbeActuallyReachesTheTests:
    self.assertNotEqual(marked.returncode, 0,
        "the probe did not reach the test session: ... so this guard would be vacuous")
```

That meta-check REQUIRES this test to fail under the probe, and it is what stops the invariance guard
over five protected files from going green-by-accident. Verified passing at review: `1 passed in 2.39s`.
Making the test ambient-independent would satisfy it for the wrong reason and silently un-guard those
files.

### BLOCKER 2: a live 42-test regression falsifies the plan's premise (F-9)

The plan and `6z5yos` both state `e4lkv5` fixed 30 of the 31 masked failures "so they now pass with the
marking present even if the scrub were removed". Measured over the five `PROTECTED_FILES`:

```text
PROTECTED FILES marked (plugin)  exit=1   42 failed, 447 passed in 252.43s
PROTECTED FILES clean            exit=0  489 passed in 84.80s

# all 42 in one file, and it IS the role refusal:
tests/test_ipd_lifecycle_cli.py marked -> 42 failed, 47 passed
AW-LIFECYCLE-ROLE-001 in output: True
sample: tests/test_ipd_lifecycle_cli.py::FinalizeTests::test_positive_finalize_succeeds_with_attribution_and_evidence

# cause, by inspection: 1 declaration across 11 classes
grep -n declare_execution_role tests/test_ipd_lifecycle_cli.py -> 332 (BeginCliTests only)
grep -n '^class ' tests/test_ipd_lifecycle_cli.py             -> 11 classes
```

It hid because the guard that catches it is excluded from a bare run:

```text
tests/test_role_declaration_guard.py:63   pytestmark = pytest.mark.slow
pyproject.toml:170  addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"
```

### E-03's deliverable already exists, and is stronger (F-8)

The plan asserts "nothing currently tests conftest's pop" / "no test found asserting the pop or its
effect". `tests/test_role_declaration_guard.py` asserts outcome INVARIANCE under both ambient roles with
the scrub deliberately defeated, and states the intent: "That makes the guard independent of the scrub:
it keeps working if the scrub is ever removed." E-03's authored assertion (ambient variable absent) is
weaker and self-referential. The genuine gap is REACH, not absence.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | OVER-SCOPE | D (anti-regression); C (architecture) | `8b9ufm` ("Do not \"fix\" it and do not let new assertions depend on ambient env"; "do not modify it"); `tests/test_role_declaration_guard.py` `_KNOWN_AMBIENT_ASSERTING` comment and `TheReassertProbeActuallyReachesTheTests` asserting `marked.returncode != 0`; that meta-check `1 passed` at review | E-02 INSTRUCTS AN EDIT AN EXECUTED PLAN FORBIDS AND THAT WOULD SILENTLY DISABLE A SECOND GUARD. `8b9ufm` declares the file and forbids "fixing" this test; its F-18 constrains NEW assertions and was misread by `6z5yos` as a design for this change. Independently and decisively, another guard uses this test's failure-under-probe as the meta-check keeping its invariance assertion over five protected files non-vacuous, so making it ambient-independent turns that check green for the wrong reason. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | Recorded as plan F-7. E-02 rewritten to ADD a differently-named test and leave the owned one BYTE-UNCHANGED, with `git diff` proof required in V-02 plus the meta-check re-run; the authored "convert the test" fallback WITHDRAWN as being the forbidden edit; Scope OUT, Deferred, scope check and the gate all carry the prohibition, the gate as a STOP condition; a conventions bullet records that a test can be unfalsifiable by one route and load-bearing for another guard. |
| PR-002 | BLOCKER | UNDER-SCOPE | A (correctness of premise); E (testing) | `42 failed, 447 passed` marked vs `489 passed` clean over `PROTECTED_FILES`; all 42 in `tests/test_ipd_lifecycle_cli.py` with `AW-LIFECYCLE-ROLE-001` present; 1 `declare_execution_role` across 11 classes; `pytestmark = pytest.mark.slow` with `addopts` excluding `slow` | THE PLAN'S PREMISE THAT THE ROLE-INHERITANCE WORK IS FINISHED IS FALSE, AND THE QUOTED FIGURE IS STALE. Both the plan and `6z5yos` assert `e4lkv5` fixed 30 of 31 so they pass with the marking present. 42 tests in a file the guard already protects still fail, because only one of its eleven classes declares a role. This matters twice: an executor re-measuring E-01 will hit it and may mistake it for their own breakage, and it is direct evidence AGAINST OQ-02's runner-side scrub, since masking is demonstrably still hiding real defects here. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as plan F-9. Concern carries the measurement and the cause; E-01 warns the executor to expect it and forbids absorbing or self-attributing it; Scope OUT, Deferred and the scope check exclude fixing it (it is `e4lkv5`'s unfinished work needing its own artifact); the gate carries it as the second STOP condition; E-04 must weigh it when answering OQ-02, and OQ-02's rationale now records it as a fact against. |
| PR-003 | HIGH | IN-SCOPE | F (honest documentation) | same node id: `1 failed` under a re-assert plugin, `1 passed` without | THE VACUITY CLAIM IS OVERSTATED IN A WAY THAT LICENSES THE WRONG FIX. "Cannot fail for ANY ambient value" is false: the marked condition remains observable via `pytest_configure`, and this tree already exploits that. Believing the stronger claim is what makes deleting or rewriting the test look safe, which is PR-001's harm. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as plan F-6 and F-1 downgraded BLOCKER -> HIGH with the narrower statement (the ORDINARY exported route is dead, the plugin route is not); E-01 must measure BOTH halves and V-01 requires both pasted; a conventions bullet names `_REASSERT_PLUGIN` as the in-tree reference; the stale line in the 2026-09-23 history annotated rather than rewritten. |
| PR-004 | HIGH | OVER-SCOPE | E (testing); C | `tests/test_role_declaration_guard.py` docstring ("it keeps working if the scrub is ever removed") and `ProtectedTestsDoNotDependOnTheAmbientRole`; E-03's own text "assert the ambient variable is absent during a test session instead" | E-03'S DELIVERABLE ALREADY EXISTS AND IS STRONGER THAN WHAT E-03 SPECIFIES. The plan twice asserts nothing tests the scrub. A shipped guard asserts outcome INVARIANCE under both roles with the scrub deliberately defeated, which is what the affected tests actually need; E-03's version pins the mechanism and is self-referential, as the item concedes. Writing it as authored adds a weaker duplicate, and two tests that look redundant invite deleting the wrong one. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as plan F-8 and F-4 downgraded MED -> LOW with the corrected statement. E-03 RE-SCOPED to establish the real gap, which review measured as REACH (the `slow` marker excludes it from a bare suite, which is how PR-002 hid), with three recorded options including writing NOTHING; `tests/test_conftest_role_scrub.py` removed from `- Scope-Paths:` since no file may be needed; V-03 accepts a no-test outcome; spec-sync asks for a cross-reference between conftest and that guard, whose mutual absence caused this error. |
| PR-005 | MEDIUM | IN-SCOPE | F (honest documentation) | both items under `.aw/records/backlog/done/` | THE TWO CLOSES THE PLAN LEAVES AS OWED ARE ALREADY DONE. `8bif6g` and `t49rmq` are both `- Status: done`, so the Deferred bullet describes records work that does not exist and an executor would hunt for it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as plan F-10; F-2 and the Deferred bullet corrected; the stale history line annotated inline with a dated marker rather than rewritten. |
| PR-006 | MEDIUM | IN-SCOPE | F (honest documentation); D | conftest's "which is what every such test already does" against the 42 non-declaring tests; conftest's `31 failed, 8080 passed` against the measured 42 | THE CONFTEST COMMENT BLOCK OVERSTATES COMPLIANCE, AND THAT IS HOW PR-002 SURVIVED. It claims every test needing the marking sets it itself, which the 42 inheriting tests contradict, and its measured figure is stale. The plan quotes that block as authority (reasonably) without checking either claim, so a false comment propagated into a plan's premise. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Spec-sync now requires correcting both claims if the block is touched, and adding a cross-reference to `test_role_declaration_guard.py`; the conventions bullet restating "every such test already does" is corrected in place with the measurement. |
| PR-007 | LOW | UNDER-SCOPE | E (testing); G | `ChildEnvWorkerRoleTests.test_both_drivers_mark_only_an_isolated_turn`, which drives both hosts' real turn functions and asserts four halves including "(d) A STALE VALUE IS STRIPPED" | E-02 MAY BE ASKING FOR A TEST THAT LARGELY EXISTS, IN THE SAME CLASS. The sibling test already captures the child env from both hosts and asserts that a non-isolated turn's child carries no marking even when the driver's own environment holds a stale one, which is close to the property E-02 wants. The plan neither cites it nor tells the executor to check it, risking a near-duplicate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires reading that test FIRST and extending its established pattern, and permits the outcome "already covered, here is the evidence"; OQ-01 gains that as candidate (c) and names it the first thing to check; V-02 accepts it as a satisfying answer. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02's edit is forbidden. Delete E-02, or re-aim it? | RE-AIM: E-02 now ADDS a differently-named test at the env-construction seam and leaves the owned test byte-unchanged. | DELETING E-02: rejected because the property (the driver's own env must never be worker-marked) is real and currently has no falsifiable assertion through an ordinary run, which is `6z5yos`'s legitimate core. Keeping E-02 as written with a warning: rejected because the plan already carried warnings and still instructed the edit, and because the harm is silent (the meta-check would pass for the wrong reason, so nothing would go red to say so). | `8b9ufm`'s two prohibitions; `_KNOWN_AMBIENT_ASSERTING` and its meta-check; `plan-review.md` 2.4 | yes |
| D-2 | Should the review fix the 42-test regression it found? | No. Reported, excluded from scope, and given a STOP condition. | FIXING it here: rejected on two grounds. It is `e4lkv5`'s unfinished work in a file this plan does not declare, and it is ten classes of `setUp` changes, which is larger than this plan's entire subject; absorbing it would void the scope fence. Staying silent: rejected outright, because an executor re-measuring E-01's premise WILL hit it and would otherwise either self-attribute it or conclude their own change broke 42 tests. | the measured 42-vs-0 split; `plan-review.md` 2.2 (record, do not absorb); the plan's own `- Scope-Paths:` | yes |
| D-3 | Should this review file a backlog item or plan for the 42-test regression? | No, and this is a deliberate limit of a read-only review. It is recorded in the plan (F-9) and in this record, and the plan's Deferred section says it needs its own artifact. | FILING an item: rejected because `/plan-review`'s contract is to review and revise the plan, not to create unrelated records; a review that quietly files artifacts is doing work nobody reviewed. STATED PLAINLY AS A GAP: if no successor artifact is created, this finding lives only in this plan's prose, which is weaker than a tracked item. The maintainer should file one. | `plan-review.md` scope ("Review planning documents only"); AGENTS.md (a review reports and waits); raised with maintainer | no |
| D-4 | Does F-9 resolve OQ-02 against a runner-side scrub? | No. OQ-02 stays open with F-9 recorded as evidence against. | RESOLVING it to refuse: rejected because the maintainer may legitimately weigh a managed target repo's false baseline above this repo's masking problem, and the trade is theirs (it is a runner behavior change on a load-bearing safety marker on both hosts). Ignoring F-9 in OQ-02: rejected because it is the strongest new evidence bearing on the question. | `plan-review.md` Step 3.1 (never guess a human decision); the plan's own `Owner: maintainer` | yes |
| D-5 | Is `- Blocks-Release: next` still earned, given F-1 was downgraded? | Yes, left in place. | CLEARING it: rejected. `6z5yos` itself carries `- Blocks-Release: next` with `Priority: high`/`Work-Kind: bug`, as do `8bif6g` and `t49rmq`, all under the live-bug policy. A safety guard that cannot be falsified by an ordinary run still reports green without checking, which is the false-evidence class the policy targets; what changed is the BREADTH of the vacuity, not its existence. F-9 independently strengthens the case that this family is not finished. | `6z5yos` front matter; AGENTS.md live-bug policy | yes |
| D-6 | E-03's premise is false. Delete E-03, or re-scope it? | RE-SCOPE to "establish what is genuinely missing", with writing nothing as an explicit legitimate outcome. | DELETING E-03: rejected because review DID find a real gap in the same area (the existing guard is `slow`, so a bare suite catches none of this, which is how the 42 failures hid), and that gap deserves a recorded decision even if the answer is "the slow tier is the right home". Keeping it as authored: rejected as a weaker duplicate of a shipped guard. | `test_role_declaration_guard.py`'s docstring and marker; `addopts`; the measured four-minute cost of the marked leg | yes |

### Deferred and open

No finding is DEFERRED or REPLAN. Every finding above is FIXED, so no escalation to a `- Blocking: yes`
question is owed under the `review_findings_gate` rule (default `block_at: HIGH`; no
`review_findings_gate` key is configured in `.aw/config/project.json`).

OQ-01 and OQ-02 both remain OPEN by design. OQ-01 had one option WITHDRAWN as forbidden and one added;
OQ-02 gained evidence against without being resolved (D-4). Both are `- Blocking: no`, and a non-blocking
open question does not make a plan `NO-GO`.

ONE ITEM NEEDS A HUMAN AND IS NOT A FINDING AGAINST THIS PLAN (D-3): the 42-test role-inheritance
regression in `tests/test_ipd_lifecycle_cli.py` has no tracked artifact. This review deliberately did not
create one, because a review reports and waits. It should be filed.

### Notes on what was NOT changed, and why

- No code or test file was touched by this review. Only the plan under review and this record. Every
  probe ran read-only or in throwaway directories under the lane's own `.aw/state/`, each removed
  afterwards; the lane tree was verified clean before and after.
- `tests/test_worker_role_refusal.py` and `tests/test_role_declaration_guard.py` were NOT modified, which
  is the same restraint this review now requires of the executor.
- THE 42 FAILING TESTS WERE NOT FIXED (D-2). They are real, they are measured, and they belong to another
  plan's unfinished work.
- F-2, F-3 and F-5 were NOT retracted. All three re-measured TRUE.
- F-1 was NOT retracted despite the downgrade: the ordinary exported-variable route really is dead, and
  that is worth an assertion. Only the claim's BREADTH was wrong.
- `- Blocks-Release: next` was left in place (D-5), resting on the carrier items' own fields.
- `- Highest E allocated: 04` is unchanged and the E/V bijection stays 4/4. E-02 and E-03 were re-aimed
  rather than removed, so no renumbering occurred.
- The plan's `- Status:` is left at `to-review` in the file; the transition to `reviewed` is applied
  through `aw ipd set reviewed` so it carries an attributed history line, per the untooled-status gate.
