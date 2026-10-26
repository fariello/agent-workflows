# Check R1: References

Check every citation in the plan. Until the citation resolver exists (Order 03, Stage 2), the agent checks every citation in the plan itself, locating each by symbol, heading, or quoted text (spec Section 4.2 row R1), and records `not-found`/`ambiguous`/`moved` results as findings per `_findings.md`.

For each eligible plan:
1. Read the whole plan.
2. List material files, requirements, issues, ADRs, APIs, schemas, tests, and
   behaviors it relies on.
3. Open the referenced evidence.
4. Verify material claims with `path:line` evidence:
   - Locate the cited construct by symbol, heading, section ID, or quoted string, treating the line number as a hint (spec `ipd-structure-and-linting` Section 10.2).
   - Disposition:
     - Anchor resolves and only the line moved: no finding, or at most one LOW batched finding per plan noting the drift.
     - Anchor does not resolve anywhere, or resolves to something that contradicts the claim: a real evidence finding at the severity of the claim it supports.
     - Bare `path:line` with no anchor that no longer matches: search for the described construct before judging, and record which case applied.
   - Costlier error: rejecting a citation the reviewer merely failed to re-locate is WORSE than under-reporting drift, because a review finding is durable and tracked while drift is not. Measured in this repository: backlog `88manw` recorded that plan `si24ia`'s review finding PR-305 rejected a correct spec section citation and substituted a wrong one, which subsequent readers propagated. The rule covers section or heading anchors in specs and docs, not only code symbols.
   - Git ref asymmetry: the same costlier error rule applies to git citations. The trigger is narrow: ONLY when a reviewer is about to declare that a branch, lane, or commit cited as evidence no longer exists. `git branch -a` answers a question about REFS while the evidence lives in OBJECTS. Before declaring lane or branch evidence unrecoverable, a reviewer must search dangling objects by subject (e.g. via `runner_shared.find_dangling_commits_by_subject` or `git fsck --connectivity-only`), and must record which check was run. Precedent: backlog `1ffh63` recorded that review finding PR-001 on plan `kl18sz` declared a replay source unsatisfiable on a refs-only reading and weakened V-01 to a 4-path substitute plus a synthetic fallback, while the finalize tip was resolvable and the real replay was LARGER than claimed. Limits: dangling objects are LOCAL to one checkout, are NOT cloned, and expire to gc; a resolving dangling commit is a legitimate evidence source and NEVER a durable archive, and a plan must not be written to depend on one persisting.
5. Record missing, stale, contradictory, or inaccessible evidence.
6. Do not infer unsupported implementation details.

If missing evidence prevents reliable review, file a finding or open question.

Record notes in the review record's `### Step R1` subsection starting with `- Checked: <what was examined>`.
