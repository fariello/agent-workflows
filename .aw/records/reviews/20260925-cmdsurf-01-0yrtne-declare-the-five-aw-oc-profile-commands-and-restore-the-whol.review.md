# Review: Declare the five aw oc profile commands and restore the whole-CLI declaration test

- Subject-Id: 0yrtne
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `e768d9c8` (the plan cites `0c2e7970`, which is an ancestor; both were
checked and the measurements agree). The target plan was committed and unchanged, so the pre-review
snapshot was correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent`
reported `conforming` (exit 0) BEFORE review and again at `--phase review-finalize` afterwards.

ALL THREE OF THE PLAN'S FINDINGS HOLD AND ITS DIAGNOSIS IS CORRECT. F-1: `find_undeclared_leaves`
returns exactly the five `oc profile` leaves. F-2: the guard test was deleted in `19313eed`, and the
only remaining checks are narrowed to their own verbs (`test_host_capability_extension.py` filters to
leaves starting `host`, `test_prompts_new.py` asserts only that `prompts new` is absent from the set,
its comment conceding the suite-wide test "is RED at baseline for other verbs"). F-3: five stale
citations of the deleted `test_cli_conformance_matrix.py` remain. OQ-01 is resolved correctly and its
reasoning (a `slow` mark is why the regression went unnoticed) is the right lesson; I re-measured the
check at 0.27s rather than the plan's 0.4s and corrected it, which strengthens the same conclusion.

THE DOMINANT FINDING IS PR-701, AND IT IS THE ONE THE PLAN'S OWN GOAL DEMANDS. The Goal sentence is
"a fast test fails the moment a new parser leaf ships without one." As written the plan could not
deliver that: the CI job literally named `output-conformance ... (fail-closed)` lists three test files,
and ALL THREE ARE ABSENT. So after this plan lands, the restored test runs in the bare suite and the
job that claims to gate the contract still runs nothing. The plan's Scope explicitly excluded "restoring
any other deleted test", which is right, but it did not distinguish that from REPAIRING THE STEP THAT
NAMES THEM, which costs two lines and is the difference between achieving the goal and half achieving
it. I added E-04 for the repair and E-05 for the citations, and recorded the maintainer's escape hatch
in OQ-02: E-04 can be dropped without touching E-01..E-03.

I CORRECTED A FALSE MEASUREMENT THAT IS CIRCULATING BETWEEN PLANS, which is the finding I would most
want a reader to notice. Sibling plan `8ud1is` states in three places, including a review record I
wrote in this same sweep, that the CI step "collects nothing and exits 0" and therefore passes
silently. I ran the step's exact command three times: it exits **5**, which is
`pytest.ExitCode.NO_TESTS_COLLECTED`, and 5 is NONZERO, so the step FAILS and the job goes red. The
honest diagnosis is different and is actually more interesting: the job was `success` on all six Python
versions in the last recorded run (`gh run view 35956980850`), and `19313eed` (dated 2026-09-24 17:13)
landed AFTER the newest recorded `tests.yml` run (2026-09-24 04:45), so the breakage is real but has
NOT YET BEEN EXERCISED. "Broken and unobserved" and "silently green" call for different responses: the
first is caught the next time CI runs, the second never is. The plan now carries the measurement and an
explicit instruction not to inherit either number without re-measuring. This also means my own earlier
review record on `8ud1is` carries a wrong claim; it is round-1 history there and I have not edited it,
but this record is where the correction lives.

THE SECOND CLUSTER, PR-702 THROUGH PR-704, IS THE SAME UNDERLYING PROBLEM THREE TIMES: the items
delegated a decision to "read it from the parser" or "read the handler", where the source they named
does not actually contain the answer. This matters more than it looks, because a `CommandDeclaration`
is a set of CLAIMS about a command and a wrong field is a false entry in the normative inventory.
(a) E-01 named `oc update-models` as the model for two READ leaves; it is declared `mutation`.
(b) `legacy_flags` "taken from the parser" yields `-h/--help/--no-color/--color` on every leaf, and
across all 141 existing declarations those three appear ZERO times and `--no-color` only on bare `aw`;
a literal reading would add four wrong flags per leaf. (c) `exit_contract` is not in the parser at
all, and two of the three writers have a real exit-1 path that a copied `(0, 2)` would erase: a
declined wizard returns 1, and a declined removal prints "Nothing was changed." and returns 1. I drove
all ten paths with a throwaway `XDG_CONFIG_HOME` rather than reading them, which is what turned up the
exit-1 pair. 26 of the 68 existing mutation declarations legitimately omit `1`, so neither shape is
automatic and the measurement was necessary.

PR-705 IS THE FIELD NOTHING WILL CHECK, and it is worth stating plainly because the plan's narrowness
creates it. `empty_error_renderer` was not mentioned in either declaration item. The deleted file's
`test_empty_error_renderer_classification_consistency` enforced it against an allowlist of query
commands BY NAME, and this plan restores 1 of that file's 14 tests, so that check is gone. Measured:
`_oc_profile_list` calls `term.empty_result` on the no-profiles path, which is exactly what
`shared_empty_result` denotes, while `show` has no empty state at all. So the two leaves take DIFFERENT
values, an executor had no instruction, and no test would have caught a wrong guess. E-01 now states
both values with the basis, and V-01 demands the basis be pasted.

ON RIGHT-SIZING, the original four items were not merely count-passing; E-01 and E-02 each bundled
three fields whose answers came from three different kinds of evidence (a parser dump, a handler read,
and a driven exit code). I did not split them further, because the natural split is by leaf rather than
by field and that would produce five near-identical items; instead each item now names the measurement
per field, and the V-items demand the evidence per field. The plan grew from four items to six, with a
6:6 bijection.

ONE THING I CHECKED THAT STRENGTHENS THE PLAN rather than weakening it: I confirmed the alias question
the plan never had to ask. `discover_parser_leaves` de-duplicates argparse aliases by object identity,
so `profiles`, `ls` and `rm` do NOT surface as leaves and must not be declared; the undeclared set is
five, not eight. A plausible executor could have declared eight and introduced declared-but-absent
drift. Likewise the family ROOT `oc profile` must not be declared. Both are now in the conventions
section. I also verified that the restored test's name makes an existing comment in
`agent_workflows.lane_containment` TRUE again rather than stale, so E-05 says to verify it, not rewrite
it.

Backlog item `4fe3al` carries `- Blocks-Release: next` and `- Work-Kind: bug`, and the plan correctly
inherits both, so the release gate is preserved by the handoff. The plan's gate now says so explicitly
and states that no separate de-gating is required.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | UNDER-SCOPE | E. Testing / G. Plan executability | The `output-conformance` step names `tests/test_cli_conformance_matrix.py`, `tests/test_cli_quality_gates.py`, `tests/test_cli_output_docs_rollout.py`; all three absent; the step's exact command exits 5 three runs in a row; the plan's Goal sentence promises a test that fails "the moment a new parser leaf ships without one" | THE PLAN CANNOT MEET ITS OWN STATED GOAL, because the CI job that claims to gate the declaration contract runs no test at all. After E-01..E-03 the restored guard would run only in the bare suite, while the job named "fail-closed" still lists three files that do not exist, including one this plan does not restore. Scope correctly excluded restoring other tests; it did not distinguish that from repairing the step that names them, which is two lines and is what makes the guard a gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low (two lines in one file, verifiable locally by running the step's own command) | FIXED | Added E-04 (repair the step to name only the restored test, and prove a missing file FAILS) with V-04, and E-05 (repoint the six stale citations) with V-05. Scope and Scope-Paths extended to `.github/workflows/tests.yml` and `CONTRIBUTING.md`; the two unrestored harness files are recorded in Deferred so the step never again names a file nothing restores. OQ-02 records the reasoning and the maintainer's escape hatch. Added F-4. |
| PR-702 | MEDIUM | IN-SCOPE | A. Correctness (a false model) | `get_declaration("oc update-models").command_class` -> `mutation`; original E-01 said "modelled on the existing `oc update-models` entry" for two `read` leaves | THE ITEM NAMES A MUTATION AS THE MODEL FOR TWO READ LEAVES. An executor following the instruction literally would copy a mutation's output shape (`human_recipe="status"`, `renderer_boundary`) onto two query verbs, and `command_class` is not cosmetic: `conformance_matrix.required_scenarios` derives required coverage from it, so a wrong class asserts the wrong contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now names the true analogue (the `_oc_profile_out` boundary path) and states `human_recipe` per leaf with the basis: `table` for `list` (it prints `format_table`), `detail` for `show` (it prints `preview_lines`). Added F-5. |
| PR-703 | MEDIUM | IN-SCOPE | A. Correctness / G. Plan executability | Across 141 declarations `-h`/`--help`/`--color` appear 0 times and `--no-color` only on bare `aw`; the parser reports all four on every `oc profile` leaf; original E-01/E-02 said `legacy_flags` "taken from the parser (read them from the parser, do not guess)" | THE INSTRUCTION TO READ THE PARSER PRODUCES FOUR WRONG FLAGS PER LEAF. `legacy_flags` records the verb's OWN surface, not the shared presentation parent, and the convention is visible only by comparing against the whole inventory, which the item did not say to do. Following the item literally yields five declarations that differ in shape from every other one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both items now carry the EXACT measured tuples per leaf and an explicit exclusion rule with the census behind it. V-01 requires confirming no presentation flag appears. Added F-7(a) and a conventions bullet. |
| PR-704 | MEDIUM | IN-SCOPE | A. Correctness (an unstated field with a non-obvious answer) | Driven with a throwaway `XDG_CONFIG_HOME`: a declined removal returns 1 (`cli._oc_profile_remove`, "Nothing was changed."), a declined wizard returns 1 (`cli._oc_profile_add`); `oc profile default` has no exit-1 path (set -> 0, no-args -> 2); 26 of 68 existing mutation declarations omit `1` | `exit_contract` IS NOT IN THE PARSER AND THE ITEMS NEVER MENTIONED IT, so its value would come from copying a neighbour. Two of the three writers have a real exit-1 decline path that a copied `(0, 2)` erases, and `default` genuinely has none, so no single value is right for all three. Since a quarter of existing mutations legitimately omit `1`, an executor has no way to infer it and would misdeclare either two leaves or one. | C:Low; U:Low; S:Low; F:Medium (a false exit claim in the normative inventory); Overall:Low | FIXED | E-02 states `(0, 1, 2)` for `add`/`remove` and `(0, 2)` for `default`, each with the handler quote behind it, and warns that neither shape is automatic. V-02 requires the codes be DRIVEN and pasted, not asserted. Added F-7(b). |
| PR-705 | MEDIUM | UNDER-SCOPE | D. Anti-regression / E. Testing | `_oc_profile_list` calls `term.empty_result` (quote: "no runner profiles configured"); `show` raises `ProfileNotFoundError` -> exit 2 with no empty state; the deleted file's `test_empty_error_renderer_classification_consistency` enforced this field against a by-name allowlist and is NOT among the 1 of 14 tests restored | THE ONE FIELD WITH NO INSTRUCTION IS ALSO THE ONE FIELD NO RESTORED TEST CHECKS. `empty_error_renderer` went unmentioned by both declaration items; the two read leaves take DIFFERENT values (`list` has a real empty state, `show` has none); and the test that would have caught a wrong guess is among the 13 this plan deliberately does not restore. So a wrong value is both easy and permanently unchecked. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 states both values with the measured basis and says plainly that nothing will check it. V-01 requires the `empty_result` call site be pasted as the basis for `list` and a one-line reason for `show`. The gate's honesty rule names this as one of three easily faked claims. Added F-8 and a Deferred row recording the cost of the narrow restoration. |
| PR-706 | MEDIUM | IN-SCOPE | A. Correctness (a false claim inherited from a sibling plan) | The step's exact command run 3x -> `EXIT=5`; `pytest.ExitCode.NO_TESTS_COLLECTED == 5`; `gh run view 35956980850` -> that step `success` on 3.9 through 3.14; `19313eed` dated 2026-09-24 17:13, newest recorded run 2026-09-24 04:45 | A FALSE MEASUREMENT IS CIRCULATING BETWEEN PLANS AND WOULD HAVE BEEN COPIED INTO THIS ONE. Sibling `8ud1is` states in three places that the CI step "collects nothing and exits 0" and so passes silently; it exits 5, which is nonzero, so the step FAILS. The distinction changes the response: broken-and-unobserved is caught the next time CI runs, silently-green never is. The true state is the latter's opposite: the job passed on all six Pythons in the last recorded run and the deleting commit has not yet been exercised. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 carries the measured exit 5, the run evidence and the dating, and the gate adds a DO NOT REPEAT clause instructing the executor to re-measure rather than inherit either number. V-04 forbids accepting `exit 0` as evidence. Added F-4. My own round-1 record on `8ud1is` carries the wrong claim; it is left as history there and corrected here. |
| PR-707 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: three sentences, no scope fence, no approval paragraph, no stop conditions; `- Blocks-Release: next` on both the plan and item `4fe3al` | THE GATE OMITTED EVERY ELEMENT THE CONTRACT REQUIRES BEYOND THE COMMIT RULE. No per-path scope fence (so `aw ipd finalize` reconciliation had nothing to reconcile against), no statement of what approval means, no stop conditions, an UNCONDITIONAL finalize instruction that ignores runner ownership, and no mention that the inherited release gate is discharged by the handoff. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph naming the three things (five normative contract entries, a CI job change review added, a deliberately narrow 1-of-14 restoration); a per-path scope fence as a DECLARATION, including that `lane_containment.py` is expected to need no edit and is deliberately not in Scope-Paths; the honesty rule naming the three easiest-to-fake claims; two genuine stop conditions; conditional runner/executor finalize ownership; and the `4fe3al` close with its gate handoff stated. |
| PR-708 | LOW | IN-SCOPE | G. Plan executability (citation durability) | `aw ipd lint --phase review-finalize` reported 17 `IPD-C801` advisories on the revised draft, every one a bare `file:line` offset; this plan's own E-items edit `cli.py` and `command_surface.py` | BARE LINE OFFSETS IN A PLAN THAT EDITS THE FILES IT CITES. The revision I wrote cited `cli.py` handlers by offset; E-01..E-05 change those same files, so the offsets expire during execution and then point at unrelated valid code. The rule is advisory, but the hazard is concrete here rather than theoretical, and E-05's own targets are found by grep for exactly this reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote every citation to name the SYMBOL (`cli._oc_profile_add`, `command_surface.discover_parser_leaves`) or quote a unique content string, keeping offsets only as trailing convenience. E-05 now says to find its targets by grep rather than by line number. Re-verified: `IPD-C801` advisories 17 -> 0, `aw ipd lint --phase review-finalize` reports `conforming` with `findings:0`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan says to read `legacy_flags`, `mutation_gate` and `exit_contract` from the parser and handlers. Accept that delegation, or derive the values at review? | Derive and state every value, by driving the CLI where the source does not contain the answer. | (a) Leave the instruction as-is - rejected on measurement: the parser reports four presentation flags no declaration carries, and `exit_contract` is not in the parser at all, so the named source cannot answer two of the three fields. (b) Derive only the flags - rejected: the exit-1 decline paths are the least obvious of the three and the most likely to be copied wrong from a neighbour. | 141-declaration flag census; driven exit codes under a throwaway `XDG_CONFIG_HOME`; `cli._oc_profile_add` and `cli._oc_profile_remove` each returning 1 on a decline | yes |
| D-2 | `mutation_gate` for the three writers: one value for symmetry, or per leaf? | Per leaf: `confirmation` for `add` and `remove`, `none` for `default`. | (a) `confirmation` for all three - rejected: `cli._oc_profile_default` accepts no `--yes`, prompts for nothing and writes immediately, so declaring a gate it does not have is a false claim about what protects the write. (b) `none` for all three - rejected: `add` and `remove` both refuse outright without `--yes`, which is exactly what the value denotes. | the three handler bodies; the refusal strings in `add` and `remove`; the absence of any confirmation path in `default` | yes |
| D-3 | Should this plan repair the vacuous CI step, which was not in its original scope? | Yes, as E-04, with an explicit escape hatch if the maintainer wants it separate. | (a) Leave it out - rejected against the plan's OWN Goal sentence: the guard would run only in the bare suite while the job named "fail-closed" still names three absent files, one of which this plan does not restore. (b) Also restore the other two named harness files - rejected: they depend on reviewed golden fixtures and are a much larger restoration; naming files nothing restores is what created this failure mode. (c) File it as a separate backlog item - rejected as worse than either: it would leave a knowingly broken gate in place for the duration. | the step's command exiting 5; all three named files absent; the Goal sentence; the two harness files recorded in Deferred | yes |
| D-4 | Sibling plan `8ud1is` says the CI step exits 0 and passes silently. Inherit that, or re-measure? | Re-measure, and correct it in this plan with a DO NOT INHERIT instruction. | (a) Inherit the sibling's number - rejected: it is wrong (exit 5, nonzero, the step fails), and the wrong number implies a different and less urgent failure mode. (b) Correct it silently - rejected: the claim appears in three places in `8ud1is` and in a review record I wrote in this same sweep, so an executor is likely to meet it; saying which number is measured and instructing a re-measure is what stops it propagating further. | 3 runs of the step's exact command -> `EXIT=5`; `pytest.ExitCode.NO_TESTS_COLLECTED == 5`; `gh run view 35956980850` showing that step `success` on all six Pythons before the deleting commit | yes |
