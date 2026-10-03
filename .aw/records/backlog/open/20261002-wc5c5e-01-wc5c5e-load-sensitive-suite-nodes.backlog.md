- Id: wc5c5e
- Status: open
- Set: wc5c5e
- Priority: medium
- Work-Kind: chore
- Summary: Two suite nodes fail under the parallel default run but pass in isolation: classify and either fix or document

## Workflow history
- 2026-10-02 created (aw backlog): filed from mflqqf plan authoring; measured at HEAD 4fbbc8386

Measured at HEAD 4fbbc8386 while baselining for backlog item mflqqf.

A bare `python3 -m pytest` run (the default: -q -n auto --dist=worksteal -m 'not slow and not livecorpus') reported:

  5 failed, 4622 passed, 2 skipped, 3 warnings in 410.45s (0:06:50)

Three of the five are already filed:
  tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms  -> 6bolin
  tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation -> 8jeh4x
  tests/test_selector_type_containment.py::test_must_not_refuse_matrix                                                         -> bxnhdj

TWO ARE NOT FILED, and both PASS WHEN RUN ALONE:
  tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference
  tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit

Isolated re-run of exactly those two nodes:
  2 passed in 118.59s (0:01:58)

So they are LOAD-SENSITIVE under xdist rather than standing failures. Note the isolated runtime: 118s for two tests, against conftest.py's 90.0s _DEFAULT_TEST_TIMEOUT per test. Both nodes spawn subprocesses (a CLI invocation and a typecheck run), so the plausible mechanism is that under -n auto contention each exceeds the per-test hang guard, but that is a HYPOTHESIS and the triage should confirm it from the actual failure output rather than assume it.

WHAT NEEDS DECIDING, which is why this is filed as a chore and not a bug: a load-sensitive test may be (a) a defect in the test, which should be given an explicit @pytest.mark.timeout budget or made cheaper, (b) a real concurrency or resource bug in the code under test, or (c) an accepted property of a 4600-test parallel run that should be documented. Classifying it as a user-perceptible defect would overclaim; the repository's own rule is that an unmeasured hunch is not a bug.

WHY IT MATTERS: the default suite is the gate every lane and every plan executor is judged against. Two nodes that fail under load make the honest bar 'no newly failing test' rather than 'green', which means every executor must re-run every red node in isolation to classify it. That is a real cost paid on every plan, and it also erodes the signal, since a reader who sees a habitually red suite stops treating red as information.
