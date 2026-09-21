- Id: eozq91
- Status: open
- Set: eozq91
- Priority: medium
- Work-Kind: chore
- Summary: spec 7ckptx is approved while all 42 of its requirements are implemented by 8 executed plans, so attention reports a finished spec as not-started

## Workflow history
- 2026-09-20 created (aw backlog): spec 7ckptx is approved while all 42 of its requirements are implemented by 8 executed plans, so attention reports a finished spec as not-started

MEASURED 2026-09-20 at HEAD 96e93f8c by research survey vkub9o (plan si24ia), which was surveying requirement addressability and found this as a side effect.

WHAT IS WRONG. Spec 7ckptx (.aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md) carries `- Status: approved`. Its implementing Set `lanectn` is COMPLETE: all 8 plans (h0zljh order 0, cqx5v7, nna8yz, lhmrhx, y5od1h, xdr83v, 604wra, 4fodkt) are in .aw/records/plans/executed/. All 42 of the spec R<n>.<n> requirement ids are cited by those executed plans (0 cited by no plan at all), and plan 4fodkt V-09 records the verification verbatim: "all 31 live acceptance criteria PASS with pasted output at HEAD e299a9a5" and "THE EXPLICIT SET VERDICT: the Set IS demonstrably complete against spec 7ckptx Section 4".

WHY IT MATTERS. `attention_contract._SPEC_MAP` maps spec `approved` -> READY, so `aw attention` reports a spec whose work is finished as work waiting to START. 4fodkt finalized 2026-09-17, so this has been true for at least 3 days.

THIS IS NOT A TOOL BUG. Plan 4fodkt deliberately did NOT transition the spec, and it was right not to: an agent may not set a spec `implemented`, that transition needs a cited evidence citation and is the maintainer decision. So the fix is a human act, not code.

RECOMMENDED ACTION. The maintainer reviews 4fodkt evidence and, if satisfied, runs `aw specs set <7ckptx> --status implementing` then `--status implemented --evidence <path to 4fodkt>` (or whatever the transition table requires from `approved`). If the maintainer is NOT satisfied, the honest outcome is to name which criteria are outstanding, which is information nothing currently records.

WORTH NOTING FOR THE f1sw71 QUESTION. Survey vkub9o treats this as the strongest single instance of the harm backlog f1sw71 describes, AND as evidence that a requirement-coverage mechanism would have bought little here: the coverage WAS computable from existing citations with no new mechanism, and what blocked closure was the human transition, which no mechanism replaces.
