<!-- Durable turn-2 skeptical self-audit prompt fed by tools/agy_run.py after the execute turn, resumed in the SAME conversation. The literal token {IPD_PATH} is replaced with the executed plan's path. Version-controlled on purpose. -->
Perform a skeptical post-execution audit of this executed Implementation Plan Document:

`{IPD_PATH}`

Approach this audit with rigorous skepticism. Do not assume the prior implementation is complete, compliant, or free of regressions. Treat all prior claims, checkmarks, status changes, summaries, commit messages, and assertions that "tests pass" merely as hypotheses requiring independent, reproducible evidence.

Procedure:

1. Read `AGENTS.md` and repository instructions governing IPDs, validation, commits, and scope fences.
2. Re-read the IPD, its controlling specification, and requirements. Verify the intended behavior, safety properties, interfaces, fail-closed behavior, and edge cases.
3. Inspect actual git diffs and current codebase files. Do not infer implementation from filenames or summaries.
4. Construct an evidence table containing every `E-*` and every `V-*` item: state the exact requirement, files and symbols inspected, relevant tests, commands run, result (`satisfied`, `partially satisfied`, `not satisfied`, or `not independently verifiable`), and concrete reasoning.
5. For EVERY test that backs a requirement, confirm falsifiability: verify that breaking the implementation causes the test to fail (RED) and restoring it passes (GREEN). Paste the actual red-then-green proof.
6. Verify symbol wiring: confirm that all new or updated classes, enums, flags, and policies are actively consumed and enforced in the production code path.
7. Run every required validation command and the FULL test suite with the canonical command `make test` (parallel `pytest -n auto`; fall back to `python3 -m unittest discover -s tests -t .` only if `make test` is unavailable). Paste actual command outputs and exit codes.
8. Check for common pitfalls: shallow tests, circular assertions, missing negative cases, side effects in read-only operations, or regressions in existing tests.
9. Fix every safely correctable in-scope gap immediately. Commit path-scoped (`git commit -m msg -- <paths>`). Do NOT move the plan to `executed/` or declare completion—the orchestrator verifies and completes the lifecycle transition.
10. If any gap exceeds scope or requires a human decision, stop and report the exact blocker.

Report back with:
- Verdict: `CONFORMING`, `CONFORMING AFTER CORRECTIONS`, or `NOT CONFORMING`
- Reconstructed intent and objectives
- Complete E/V evidence table with explicit evidence for every item
- Falsifiability proofs for requirement-backing tests (red-then-green output)
- Full-suite test result with actual runner output
- Findings and corrections made (files, symbols, rationale)
- Remaining blockers or open questions (if any)
- Diff and commit summary
- Explicit statement of evidentiary honesty (no fabricated findings, no unverified certifications)
