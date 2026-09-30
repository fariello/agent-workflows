# Review findings: plan rwvzqm

- Subject-Id: rwvzqm
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1101 (HIGH, fixed), PR-1102 (HIGH, fixed), PR-1103 (MEDIUM, fixed), PR-1104 (MEDIUM, fixed), PR-1105 (LOW, fixed)

## Round 1

Reviewed at HEAD `6c2a4870` in an isolated review lane. The plan file was already committed and identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming`, exit 0, with ZERO findings before semantic review, and `--phase
review-finalize --agent` still reports `conforming` with zero findings after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. `aw check plans` reports no finding
against this plan before or after revision.

THE PLAN'S CASE IS SOUND AND ITS CENTRAL EVIDENCE ALL RE-MEASURES, so I record that before the findings. I
drove the full matrix by subprocess with `cwd` in both a fresh `git init` and a non-git temporary directory
outside the repository, and F-02 reproduces exactly: `next`, `att`, `todo`, `attention`, `ipd` and `ipd board`
each exit **3** on the human surface and **2** with `--agent`, all 24 rows, with stdout empty and the
diagnostic on stderr on every human row and the record on stdout on every machine row. `rg -n "return 3$"
agent_workflows/` returns exactly the two sites the plan changes. The declarations are as F-04 says at the
values that matter: `next` is `(0, 1, 2)` and `ipd board` is `(0, 2)`, so neither admits 3. F-06's count is
exactly eight, and I confirmed each one. F-03's four quotes are verbatim in all four files, including
`agent_schema`'s "Field 'exit' must be an integer in (0, 1, 2)". F-07 is exact: three live citations of
`tests/test_awretrofit_project_root_climb.py` and no such file on disk. F-12's control holds (`--check` and
`--check --agent` both exit 0). F-13 holds (one spec, `command-surface-redesign`). F-08's blast radius holds:
the single `assertEqual(rc_h, 3)` at `tests/test_attention.py` is the only in-tree consumer, and the one other
file mentioning "no_project" is unrelated. `artifact_types.EXIT_CANNOT_RUN` exists and `cli.py` already
imports that module, so E-02's constant is available without a cycle. Every cited artifact resolves:
`c6vs7y` (graduated), `5x195l` (done, and the quoted closing note is verbatim), `bjgqez` (pending), `858lhj`,
`cn5np0`, `5gmi12`, and decision `03-quqyc4-D1`. `D156` is still the last entry in `DECISIONS.md`, and the
pending 2.0.0 CHANGELOG entry exists.

PR-1101 IS THE FINDING THAT CHANGES WHAT E-05 SHOULD BUILD, AND IT INVERTS THE PLAN'S DEEPEST CLAIM. The plan
states, twice and emphatically, that the structural hole is that NOTHING compares a declaration to an observed
exit code, and that `exit_contract` is "referenced in exactly one place in the whole test tree". Measured: it
is referenced in FIVE test files across 12 hits, and one of them,
`tests/test_run_cli_declarations.py::test_runs_resume_declared_exit_codes_are_reachable`, does precisely what
E-05 describes as missing. Its own docstring reads "Drive the real CLI in a subprocess for each of 0, 2, 5, 7
and verify it is in decl.exit_contract", and its body asserts `res_0.returncode == 0` then `assert 0 in
decl.exit_contract`, repeating for each code. It even carries the NEGATIVE form this plan most wants, a test
asserting `3 not in decl.exit_contract` with the comment "Exit 3 is absent from exit_contract, and
mechanically unreachable". And it reaches the declaration through a narrow accessor,
`command_surface.get_declaration("runs resume")`, which E-05 does not mention and which is the better tool
than `get_all_declarations()` plus a filter. The gap E-05 addresses is REAL but narrower than stated: it is
missing per-verb coverage for these two leaves, not an absent capability. That distinction matters because
E-05 as written would have produced a second convention for a job the repository already has one for, and
because the plan's Goal and its Workflow history both rest the justification on a claim that is false.

PR-1102 IS TWO MEASURED DETAILS E-05'S LOOKUP DEPENDS ON, ONE OF WHICH WOULD HAVE CRASHED IT. F-04 says the
three aliases "declare no contract of their own and inherit `next` as `canonical_command`". Measured, each of
`att`, `todo` and `attention` carries its OWN `exit_contract=(0, 1, 2)` with `command_class="alias"` beside
`canonical_command="next"`, so they can be asserted directly rather than resolved through the canonical name.
More importantly, bare `ipd` has NO DECLARATION AT ALL: the declaration key is the `command` field in bare
form, `get_declaration("ipd board")` resolves and `get_declaration("ipd")` returns None. E-05 tells the
executor to "find the entries for `next` and `ipd board`" while E-01 and E-03 drive six spellings including
bare `ipd`, so a natural implementation looping the six spellings hits a None and either raises or silently
skips a verb the plan believes it is pinning. Neither outcome is visible from the plan text.

PR-1103 IS A VALIDATION THAT CANNOT PASS AS WRITTEN, AND THE PLAN INHERITED THE ERROR FROM THE CODE. V-02
requires pasting `rg -n "exit_code=3" agent_workflows/` "showing no executable site builds one", and the
Required-tests section lists the same grep as a confirmation. Measured, that grep returns FOUR hits at base
and every one is inside a comment explaining why such a record is unemittable. E-02 explicitly requires that
reasoning be RETAINED, so an empty grep is not merely unachieved but forbidden, and an executor comparing the
output against an implied empty result cannot tell pass from fail. The root of it is in the code: the `cli.py`
comment asserts that after its change the grep "finds NO site", which was already false when written, because
the sentence making the claim is itself a hit. That is the same defect class E-08 exists to repair, a comment
naming evidence a reader cannot reproduce, so I folded its correction into E-02 where the comment is already
being rewritten.

PR-1104 is the live-count convention. F-14 records `3246 passed, 2 skipped` and both the Required-tests
section and V-07 instruct reconciling the final total against it. The bare suite is `3387 passed, 2 skipped`
at review HEAD, +141 from unrelated work in a day, so an executor following the instruction literally must
account for a delta that has nothing to do with this change, and the cheapest escape from an impossible
reconciliation is to wave it through, which is exactly what V-07's own wording forbids.

PR-1105 is a carrier that does not own its row. The `--dir <non-project>` deferred row names plan `bjgqez` and
backlog `ci9kx2` in its prose and then carries `Carrier: 5gmi12`, which is a different defect entirely
(`--dir` at a SUBDIRECTORY of a real project silently under-reporting, per that item's own Summary). It passes
every mechanical gate because `aw check` validates that a carrier RESOLVES, not that it owns the stated
subject.

THINGS I CHECKED THAT PRODUCED NO FINDING. The two-verb narrowness of E-05 is correctly argued and F-06's
eight declarations genuinely would fail a tree-wide subset assertion, so the deliberate limit is right, though
I did note `runs resume` is `(0, 2, 5, 7)` where F-06 lists `(0, 3)`; the count and the conclusion are
unaffected and the row is dated context, so I left it. E-02's instruction to take the value from a named
constant is sound and the constant exists. The separation of E-03 (a new pin, shown RED first) from E-04 (an
existing pin that follows the fix) is well reasoned and I would not merge them. E-06's refusal to claim
tree-wide uniformity, and its instruction not to touch `cli-human-guide.md` or `README.md` because E-02 makes
them true, are both correct. OQ-01's four lines of evidence all verify, and its judgement is surfaced at the
gate for a maintainer to overrule rather than buried, which is the right shape for a breaking change; I left
it resolved. OQ-02 is properly deferred with a carrier and a trigger. F-01's claim that `c6vs7y` has no body
is accurate and its decision not to edit the item is correct.

Bare suite at review HEAD: `3387 passed, 2 skipped, 3 warnings in 58.91s`. This review changed only the plan
and this review record; no production file was modified at any point, all probes were subprocess runs or
in-process reads, and the matrix targets were created under a system temporary directory outside the
repository.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1101 | HIGH | IN-SCOPE | Rubric C (existing canonical mechanisms), G (executability) | `rg -n exit_contract tests/` -> 12 hits in 5 files, not 1. `tests/test_run_cli_declarations.py::test_runs_resume_declared_exit_codes_are_reachable` docstring: "Drive the real CLI in a subprocess for each of 0, 2, 5, 7 and verify it is in decl.exit_contract"; body asserts `res_0.returncode == 0` then `assert 0 in decl.exit_contract`; a sibling asserts `3 not in decl.exit_contract`; it uses `command_surface.get_declaration(...)` | THE PATTERN E-05 PROPOSES TO INVENT IS ALREADY SHIPPED, AND F-05'S "EXACTLY ONE PLACE" CLAIM IS FALSE. The plan rests its deepest justification on nothing comparing a declaration to an observed exit code; a shipped test does exactly that, including the negative `3 not in` form this plan most wants, via a narrow accessor E-05 never mentions. The gap is per-verb COVERAGE, not an absent capability, so E-05 as written would add a second convention for a job that already has one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-05b with the measurements and the quoted precedent; narrowed F-05's claim to these two verbs. E-05 now requires following that precedent, using `get_declaration`, and mirroring its `3 not in decl.exit_contract` negative assertion. V-05 requires showing the precedent was followed rather than a second convention started. |
| PR-1102 | HIGH | IN-SCOPE | Rubric A (correctness), G | `{d.command: d for d in get_all_declarations()}` (163 decls): `att`/`todo`/`attention` each carry `exit_contract=(0,1,2)`, `command_class="alias"`, `canonical_command="next"`; `get_declaration("ipd")` returns None while `"ipd board"` resolves | TWO DECLARATION FACTS E-05'S LOOKUP DEPENDS ON ARE WRONG OR ABSENT. F-04 says the aliases declare no contract of their own; they each do. And bare `ipd` has NO declaration, yet E-01/E-03 drive it as one of six spellings, so a lookup loop over those six hits a None and either raises or silently skips a verb the plan believes it pins. Neither is visible from the plan text. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-04 corrected on both points with the measurement. E-01 now prints all six declarations through `get_declaration` and records the `None`; E-05 must assert only the declared spellings, handle the undeclared bare `ipd` deliberately, and may assert the aliases directly. V-01 requires the six-row declaration output including the `None`. |
| PR-1103 | MEDIUM | IN-SCOPE | Rubric E (verification) | `rg -n "exit_code=3" agent_workflows/` -> 4 hits at base, all inside comments (2 in `attention.py`, 2 in `cli.py`); one of them asserts the grep "finds NO site" | V-02 REQUIRES A GREP RESULT THAT IS UNACHIEVABLE AND FORBIDDEN. All four hits are comments E-02 explicitly requires be KEPT, so an executor cannot reach an empty result and cannot tell pass from fail. The plan inherited the error from the code: the `cli.py` comment predicts an empty grep and is itself a hit, so it was false when written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now states the four comment hits are expected, requires a hit-by-hit statement that each is a comment and no EXECUTABLE site builds such a record, and declares an EMPTY grep a FAILURE (it would mean the required reasoning was deleted). Required tests reworded to a comment-only census. E-02 must correct the false sentence while rewriting that comment. |
| PR-1104 | MEDIUM | IN-SCOPE | Rubric G (live-artifact success criteria) | F-14's `3246 passed, 2 skipped` (authoring, HEAD `4ae4de08`); re-measured `3387 passed, 2 skipped` at review HEAD `6c2a4870` | A LIVE COUNT IS PINNED AS A RECONCILIATION BAR. V-07 and Required-tests both instruct reconciling the final total against `3246`; the real baseline has drifted +141, so a correct execution must account for an impossible delta, and the cheapest escape is the hand-wave V-07's own wording forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 must now RE-DERIVE and paste the bare-suite baseline with its HEAD before any edit; V-07 and Required-tests reconcile against THAT. F-14 carries both measurements labelled as a live number, and E-01's Expected outcome states that a differing suite count is NOT a stop condition. |
| PR-1105 | LOW | IN-SCOPE | Rubric G (ownership) | The `--dir` row's prose names `bjgqez` / `ci9kx2`; its `Carrier:` read `5gmi12`, whose Summary is "`aw attention --dir <a SUBDIRECTORY of a real AW project>` silently under-reports" | A DEFERRED ROW'S CARRIER DOES NOT OWN ITS SUBJECT. The row defers the `--dir <non-project>` case and names its real owner in prose, then carries a carrier for a different defect. It passes every mechanical gate because `aw check` validates that a carrier resolves, not that it owns the stated subject. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Carrier changed to `ci9kx2` (graduated, the item `bjgqez` graduated from), with the correction and the reason `aw check` could not catch it recorded in the row. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-1101: should E-05 still write a new declaration-versus-behavior test, given a shipped one already does this for `runs resume`? | YES, a new test for these two verbs, but extending the shipped convention (same accessor, same negative-assertion shape). | Extend `tests/test_run_cli_declarations.py` itself: rejected, that file is scoped to the `run`/`runs` family whose exit vocabulary this plan explicitly declines to touch, so adding two read verbs to it would blur the very boundary F-06 and OQ-02 are careful to draw. Drop E-05 as redundant: rejected, the precedent covers `runs resume` only, so `next` and `ipd board` genuinely have no such pin and the gap the plan identified is real. | The precedent's own scope (`get_declaration("runs resume")`, run-family fixtures); F-06's eight out-of-range declarations; the plan's Scope excluding the run vocabulary | yes |
| D-2 | PR-1102: should E-05 pin bare `ipd`, which has no declaration, by adding a declaration for it? | NO; assert only the declared spellings and RECORD that bare `ipd` is undeclared. | Add a `CommandDeclaration` for bare `ipd`: rejected as out of scope and a contract change in its own right, since `command_surface` is the normative surface object and adding a leaf to it affects the conformance matrix, not just this test. Silently skip it: rejected, that is the failure mode this finding is about; the absence must be visible in the test. | `get_declaration("ipd")` returning None; `command_surface.CommandDeclaration`'s docstring describing itself as the normative per-leaf contract; the plan's Scope declaring `command_surface.py` as a comment-only permission | yes |
| D-3 | PR-1103: should the false `cli.py` comment sentence be corrected here, or carried to its own item? | CORRECT IT HERE, inside E-02. | Carry it: rejected, E-02 is already rewriting that exact comment passage, so leaving a known-false sentence inside the block being edited would be a deliberate omission a reviewer would have to re-find. File it separately: rejected for the same reason plus it would create a carrier for one sentence inside a block this plan already owns. | E-02's existing mandate to rewrite both guard-site comment passages; the measured four-hit grep; the repository convention that a guard-site comment is part of the contract (the plan's own Step 0 note) | yes |
| D-4 | Is OQ-01's self-resolution of a BREAKING shipped exit-code change acceptable without asking the maintainer? | ACCEPT IT AS RESOLVED. | Re-open as `Blocking: yes`: rejected. All four of its evidence lines verify independently (the original requirement said "non-zero" not 3; both declarations exclude 3; three documents publish the three-state rule; the blast radius is one assertion), and the maintainer's own recorded inclination in `5x195l`'s audit note already matches. Crucially the plan does NOT hide the judgement: its gate paragraph tells an approver to REFUSE APPROVAL if they would rather keep 3, which is the correct way to route a reversible breaking change through a human. | F-09 (`uh295u` E-03's "non-zero" wording), F-04, F-03, F-08 all re-verified; `5x195l`'s audit note quoted verbatim; the gate's explicit refuse-approval instruction | yes |
| D-5 | F-06 lists `runs resume` as `(0, 3)`; measured it is `(0, 2, 5, 7)`. Correct the row? | LEAVE IT, noted here. | Correct the tuple: considered and declined as churn. The row's PURPOSE is to establish that eight declarations sit outside `(0,1,2)`, the count of eight is exact, and `runs resume` is a member either way, so no downstream instruction depends on the particular tuple. Recording it here keeps the observation without editing a finding whose conclusion is unaffected. | Measured `runs resume` = `(0, 2, 5, 7)`; the count of eight out-of-range declarations confirmed exactly; E-05's narrow scope keyed on the COUNT and not on any tuple | yes |
