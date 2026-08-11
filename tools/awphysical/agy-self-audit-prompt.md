<!-- Durable turn-2 skeptical self-audit prompt fed by tools/antigravity_execute_ipd.py after the execute turn, resumed in the SAME conversation. The literal token {IPD_PATH} is replaced with the executed plan's path. Purpose: force Antigravity/Gemini to actually re-do and prove the work rather than rubber-stamp it. Version-controlled on purpose; edit to tune. -->
Perform a skeptical post-execution audit of this executed Implementation Plan Document:

`{IPD_PATH}`

Read this first, because it is about YOUR track record on this work. On prior AW IPDs your execution was repeatedly sloppy and superficially compliant, and your self-audits certified work that did not actually conform. Documented failure modes you have committed - assume you may have done them again here and hunt for them specifically:

- Tests that PASS but TEST NOTHING: asserting a planted file/violation merely EXISTS instead of asserting it is REJECTED/DETECTED; asserting an enum equals itself; asserting a fixture you wrote is true. These tests cannot fail and are worthless.
- Implementing the VOCABULARY but not the BEHAVIOR: defining enums/classes/policies and wiring them into nothing, while claiming the execution item is done. The real code path (resolver/CLI/producer) was unchanged.
- Circular/self-fulfilling fixtures that just restate the expected answer.
- Running only your own handful of tests and never the FULL suite, missing regressions.
- Not touching a file/spec an execution item explicitly required.
- Overreaching lifecycle authority: moving the plan to executed/ or declaring completion, which is not yours to do.
- Signing an integrity/no-fabrication statement over work that did not actually conform.

We are tired of catching this and redoing your work. This audit is your chance to GO BACK AND ACTUALLY DO THE WORK you were supposed to do - not to rubber-stamp it. Do not trust your prior checkmarks, status changes, workflow history, summaries, commit messages, memory, or claims that tests passed; treat them only as unproven assertions. Do not fabricate findings either - a finding is valid only when backed by concrete repository evidence.

Required procedure:

1. Read `AGENTS.md` and every applicable repository instruction governing IPDs, validation, corrective work, commits, and executed plans.
2. Re-read the entire IPD and its controlling specification and decisions. Reconstruct the intended behavior, safety properties, interfaces, serialized fields, fail-closed cases, and downstream dependencies before judging the implementation.
3. Identify the commits and files that purportedly executed the IPD. Inspect their ACTUAL diffs and the current code. Do not infer implementation from filenames or commit messages.
4. Build an evidence table with exactly one row for every `E-*` and every `V-*`: the precise requirement, files and symbols inspected, relevant tests, commands actually run, result (`satisfied`, `partially satisfied`, `not satisfied`, or `not independently verifiable`), and reasoning.
5. For EVERY test that backs a requirement, prove it is FALSIFIABLE: temporarily break the implementation or fixture, run the test, confirm it goes RED, restore, confirm GREEN, and paste that red-then-green output. If a test cannot be made to fail, it does not satisfy its requirement - mark that item `not satisfied` and fix it.
6. Confirm the real code path actually changed: the enum/policy/class the IPD introduces must be consumed and enforced by the resolver/CLI/producer the IPD names. A defined-but-unused symbol is `not satisfied`.
7. Run every required validation command AND the FULL suite (`python3 -m unittest discover -s tests -t .`) yourself. Record actual output and exit status. Prior output is not evidence. A regression anywhere in the full suite that your change caused is a gap you must resolve.
8. Trace each required behavior end to end (schema -> implementation -> CLI/workflow surface -> serialization -> error/fail-closed behavior -> tests). Look for shallow tests, mocked-away behavior, missing negative cases, hidden fallback paths, side effects in read-only operations, duplicated policy vocabulary, and integrations that bypass the intended shared API.
9. Fix every safely correctable in-scope gap, then re-run focused + complete validation, applicable IPD lint, plan-index, parity, leak, and formatting checks. Inspect the final diff and prove each finding resolved without unrelated changes. Commit path-scoped; never `git add -A`; never push. Do NOT move the plan to executed/ or declare it terminally complete - the orchestrator owns that and will independently re-verify.
10. If a fix exceeds scope, conflicts with an approved specification, requires a human decision, or requires unavailable authority, STOP that part and report the exact blocker instead of inventing policy.

Report back with:

- Verdict: `CONFORMING`, `CONFORMING AFTER CORRECTIONS`, or `NOT CONFORMING`
- Reconstructed intent and objectives
- Complete E/V evidence table
- For each requirement-backing test: the red-then-green falsifiability proof (actual output)
- Full-suite result (actual `Ran N tests` output and exit status)
- Substantiated findings and evidence
- Fixes made, files and symbols changed, and why
- Remaining blockers or unverifiable claims
- Final diff and commit summary
- An explicit statement that you did not invent findings to satisfy this skeptical-review instruction, AND that you did not certify any item you could not back with pasted evidence

The audit is incomplete until every E-item and V-item has an evidence-backed disposition and every requirement-backing test has a pasted red-then-green proof. "The code looks right," your prior memory, prior checkmarks, and a generally green test suite are insufficient. Go do the work properly now.
