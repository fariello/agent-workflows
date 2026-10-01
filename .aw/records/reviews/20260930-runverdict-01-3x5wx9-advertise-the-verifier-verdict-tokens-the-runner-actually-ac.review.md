# Review findings: plan 3x5wx9

- Subject-Id: 3x5wx9
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-201 (HIGH, fixed), PR-202 (MEDIUM, fixed), PR-203 (LOW, fixed), PR-204 (LOW, fixed), PR-205 (LOW, fixed), PR-206 (LOW, fixed)

## Round 1

Reviewed at HEAD `a62a357b`. Structural preflight `aw ipd lint --phase author --agent` reported
`clean` (exit 0) before semantic review, and `--phase review-finalize --agent` reported `clean`
(exit 0) after every revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check
does not apply.

ALL EIGHT AUTHORED FINDINGS VERIFIED, AND I DROVE THE REAL CODE RATHER THAN READING IT. The pipe
literal occurs exactly three times in `runner_shared.py` and once in `tests/test_oc_runipd.py`, and a
repository-wide `*.py` scan finds it nowhere else (F-1). Both `tools/awphysical/` prompts carry
`- Verdict: `CONFORMING`, `CONFORMING AFTER CORRECTIONS`, or `NOT CONFORMING``, so the shipped comment's
"appears nowhere in this repository ... nothing is known to emit it" is false, and `git log -S` dates
that claim to `0fbb7498` (2026-09-22) against prompts added 2026-08-10 and 2026-08-16 (F-2, F-3).
`agy_run.py` carries zero `CONFORMING` and zero `map_verdict`, and its audit branch ends
`print(audit.response.rstrip()); return 0`, so no verdict from those prompts reaches the table (F-4).
`tests/test_oc_runipd.py` pins `("CONFORMING", "unverified", True, False)` and the `assertIn` of F-6
really would pass vacuously on the extended prefix. `tests/test_reporting_contract.py` genuinely does
not exist, so an executor trusting the backlog item would have opened nothing (F-7).
`tests/test_terminal_status_vocabulary.py` really does subscript the table directly (F-8).

I also executed the mechanisms. E-01's specified derivation yields exactly
`VERIFIED|CORRECTION_REQUIRED|BLOCKED|NOT CONFORMING`, is a prefix-extension of the historical
literal, and correctly omits `CONFORMING`. E-04's bijection holds in both directions. Both composers
render reachably and the schema line is extractable as E-04 assumes.

The findings therefore concern what the plan LEAVES BEHIND rather than its premise: in two places the
plan's own change would create or preserve exactly the kind of false comment it exists to remove.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | UNDER-SCOPE | Rubric A (correctness), F (honest documentation), D | `agent_workflows/runner_shared.py` comment above `VERDICT_VERIFIED`: `The three verdicts \`build_verifier_prompt\` asks the model for, verbatim from the prompt's schema line (\`"verdict": "VERIFIED\|CORRECTION_REQUIRED\|BLOCKED"\`)`; plan E-03 as authored (naming only the `NOT CONFORMING` and `CONFORMING` blocks) | THE PLAN WOULD HAVE COMMITTED ITS OWN DEFECT. E-02 makes the prompt advertise four tokens, which falsifies this third comment in two ways: the prompt no longer asks for three, and the quoted literal is no longer what it renders. It is the FIRST of the three occurrences F-1 counts, yet no E-item owned it. A plan whose stated purpose is to replace a comment asserting something measurably untrue would have shipped a new one | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now rewrites this block too, stating the three as the historically-advertised tokens whose order the renderer pins first and pointing at the derived renderer as the authority instead of quoting a literal that can go stale again. E-03's `Depends on:` changed `none` -> `E-02`, since the correct wording depends on what E-02 renders. V-02's expected surviving-occurrence count becomes ZERO (from the vaguer "only where a comment quotes history") and V-03 requires the block pasted. Recorded as F-9 |
| PR-202 | MEDIUM | UNDER-SCOPE | Rubric F (honest documentation), G | `runner_shared.map_verdict` docstring: "neither driver carries a verdict test of its own, and `tests/test_runner_refork_guard.py` fails if one grows back"; `ls tests/test_runner_refork_guard.py` reports no such file | `map_verdict`'s OWN DOCSTRING ASSERTS A LIVE GUARD THAT DOES NOT EXIST, inside the exact function this plan is about, and the Deferred section's out-of-scope entry did not cover it (that entry describes the host modules, whose citations ARE annotated). Measured: `runner_shared.py` carries 4 unannotated citations of the deleted file against 1 `19313eed` annotation, while `oc_runipd.py` carries 9 annotations and `agy_runipd.py` 6 | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now annotates the ONE occurrence inside `map_verdict`, in the shape the host modules already use. The Deferred entry now states the boundary explicitly (one in scope, three out) with a Carrier-Declined noting the class already has carriers in `1jg2m2` and `2wmwf7`, so the other three are neither silently fixed nor silently dropped. Recorded as F-10 |
| PR-203 | LOW | IN-SCOPE | evidence accuracy | `git log --diff-filter=A` dates `agy-self-audit-prompt.md` to `b629defc` (2026-08-10) and `agy-spec-audit-prompt.md` to `1ca197c7` (2026-08-16); plan Concern and F-3 attributed both to `b629defc` | A PROVENANCE ERROR IN THE PLAN'S DECIDING EVIDENCE. The two prompts were added by DIFFERENT commits. The error does not weaken the argument (both still predate the false claim), but the plan's whole case is that a stated provenance must be checkable, so its own must be right | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-3 now give both commits with their dates and note the claim postdates the later prompt by over a month |
| PR-204 | LOW | UNDER-SCOPE | Rubric E/G (executability of the stated evidence) | `runner_shared.build_verifier_prompt` signature (keyword-only `labels`); `KeyError: 'position'` raised at the `outcome = run_dir / "outcomes" / f"{item['position']:02d}-..."` line | THE V-02 EVIDENCE COULD NOT BE GATHERED FROM THE PLAN ALONE. V-02 instructs the executor to call the composer, but it requires a keyword-only `labels=` (hand-constructing `HostLabels` needs nine fields) and an `item` carrying `position`, which the plan never mentions. I hit both while verifying | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both requirements recorded in Project conventions and in V-02 (use `runner_shared.OC_HOST_LABELS`; include `position`), with the measured `KeyError` named so the executor recognizes it |
| PR-205 | LOW | IN-SCOPE | Rubric E (testing), P16 mutation sensitivity | plan V-01 ("at least two separate interpreter invocations with `PYTHONHASHSEED` differing"); V-04 (one-directional RED proof) | TWO EVIDENCE DEMANDS WERE WEAKER THAN THE PROPERTIES THEY GUARD. V-01 did not say what the seed check detects, so it reads as ceremony; measured, a set-derived ordering of these exact four tokens really does permute per seed (`=0` gives `VERIFIED\|NOT CONFORMING\|CORRECTION_REQUIRED\|BLOCKED`, `=1` gives `NOT CONFORMING\|VERIFIED\|BLOCKED\|CORRECTION_REQUIRED`). V-04's RED proof exercised only one direction of a bijection the plan itself insists must be two-way | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now requires three differing seeds, the prefix-extension check, and carries the measured permutations so the check's purpose is visible. The Required-tests RED-then-GREEN item now demands both directions plus a demonstration that the tightened pre-existing test fails on the old prompt, and a re-derived pre-change baseline (measured 195 passed at review) so a pre-existing failure is not misattributed |
| PR-206 | LOW | IN-SCOPE | plan-review Step 4 scope-fence ruling (2026-09-01) | plan gate ("stop and report rather than broadening them") and Scope check ("the correct response is to stop and report, not to broaden scope") | THE SCOPE FENCE INSTRUCTED A STOP OVER A SCOPE QUESTION, the wording the 2026-09-01 ruling identifies as stranding unfinished runner turns. A fence is a declaration the runner reconciles; the remedy for an out-of-scope edit is a `--scope-reason` at finalize | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both now state the fence is a declaration and that a genuinely required out-of-scope edit is made and justified at finalize. The gate also now enumerates the four comment regions E-03 must fix and forbids touching the other three refork citations |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The `VERDICT_VERIFIED` comment that E-02 falsifies: widen E-03 to cover it, or file it separately? | WIDEN E-03, and make E-03 depend on E-02. | (a) File separately, rejected because the plan would then knowingly ship a comment its own change made false, for however long the follow-up took, which is the precise defect it was authored to remove. (b) Add a fifth E-item, rejected as E-03 is already "correct the falsified comments" and this is a third instance of exactly that, so splitting would fragment one concern. | The comment is in `agent_workflows/runner_shared.py`, already declared in `- Scope-Paths:`, and is the FIRST of the three occurrences the plan's own F-1 counts, so it was already inside the plan's measured surface. E-03's own stated purpose ("so it no longer asserts ... the falsified claim") covers it on its own terms. | yes |
| D-2 | `runner_shared.py` carries four unannotated citations of the deleted `tests/test_runner_refork_guard.py`. Fix all four, none, or one? | FIX ONE (the occurrence in `map_verdict`'s docstring) and state the boundary for the other three. | (a) All four, rejected: the other three are in unrelated comments and sweeping them turns a four-item chore into a file-wide comment audit, which is the reasoning the plan already applies to the host modules. (b) None, rejected: the one in `map_verdict` is in the docstring of this plan's own subject and asserts a live guard that does not exist, so leaving it reproduces the defect at the plan's focal point. | `ls tests/test_runner_refork_guard.py` reports no such file; the host modules annotate their citations (9 in `oc_runipd.py`, 6 in `agy_runipd.py`) while `runner_shared.py` carries one `19313eed` annotation against four bare citations. The class already has carriers (`1jg2m2`'s docs-citation guard, `2wmwf7`'s package-source guard), so the three out-of-scope ones are not unowned. | yes |

### Verdict

APPROVE WITH REVISIONS APPLIED. Readiness `go-pending-approval`: the verdict is clean, no unfixed
BLOCKER or HIGH finding remains, and the one open question (OQ-01, whether the in-run prompt should
advertise a fourth behaviorally redundant token) carries `- Blocking: no`, which per the 2026-09-10
maintainer ruling does not make a plan `NO-GO`. Human approval is the remaining step.
