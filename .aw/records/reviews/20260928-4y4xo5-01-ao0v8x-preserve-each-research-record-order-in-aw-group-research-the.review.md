# Review findings: plan ao0v8x

- Subject-Id: ao0v8x
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `77c9ae12` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after. No pre-review snapshot was owed: the plan was committed and byte-identical to the lane input.
Every measurement was taken IN-PROCESS through `cli.main` on throwaway repos under `tempfile.mkdtemp`,
following the plan's own E-01 convention, which exists precisely to avoid the `ccbe60` hazard where a
subprocess `python3 -m agent_workflows` in a lane imports the main checkout.

THE DIAGNOSIS IS CORRECT, THE FIX SHAPE IS CORRECT, AND BOTH WERE VERIFIED BY BUILDING THE FIX RATHER
THAN BY READING ABOUT IT. Every finding reproduced:

- F-01/F-02: two records seeded at filename Orders `03` and `07`, regrouped bare, came back `-00-` and
  `-01-` at exit 0 with no warning. The root cause is exactly the three named sites:
  `start = getattr(args, "order", None)` then `start_order=start if start is not None else 0` in
  `run_set_assign`, against `start_order: int = 0` in `plan_set_assign`, formatted
  `order=f"{start_order + i:02d}"`.
- F-03: in the SAME output, the two renamed files still carried `order: "03"` and `order: "07"` in
  frontmatter under their `-00-`/`-01-` names, which is the stale-frontmatter state `f7a2kc` owns and
  is exactly why a front-matter-first resolution would preserve a value this verb corrupted. The tier
  decision is sound and the reasoning is the strongest part of this plan.
- F-04: `tests/test_awnaming_grammar_and_producers.py` was deleted in `19313eed` ("test: trim test
  suite from 9,136 to under 2,000 tests") and `grep -rn '_preserved_order' tests/` returns nothing, so
  the plans-side fix is genuinely unpinned.
- F-05: both precedents exist as described, and `plans_refs._preserved_order`'s docstring names
  `e3hzyc` and this exact defect class.
- F-06: `--order 1` over `03`/`07` yields `01`/`02` and `--order 0` yields `00`, both at HEAD, so the
  must-not-break guards are guarding something real.
- F-07: both spellings dispatch to `research_refs.run_set_assign`
  (`artifact_types.TYPE_BACKENDS["research"]["group"]`), and only the research-specific help string
  still reads `"Starting NN (default 0)."` while the shared one already says "Omit it to PRESERVE each
  artifact's existing Order".
- F-08: `research_refs.plan_mv` carries `order=parsed.order`, so the sibling verb in the same module
  already trusts the filename tier.
- F-10: verified verbatim and it is the correction that most raises the severity. The spec's `<NN>`
  bullet reads "`00` is the originating prompt (Section 4.6); `01..NN` are members" and its Section 5.8
  schema repeats `order: 02  # read/execute order within the set (00 = originating prompt)`. So a bare
  regroup does assert that an arbitrary record is the set's originating prompt.
- F-11: the group row of the verb table shows `[--order N]` as optional.

THE FIX WAS APPLIED IN THIS LANE AND MEASURED. Three edits (signature to `Optional[int] = None`, drop
the `else 0` collapse, resolve `order=` from `parsed.order` when `start_order is None`) produce: bare
regroup preserving `03`/`07`, `--order 1` yielding `01`/`02`, `--order 0` yielding `00`, the
tier-disagreement case following the filename, and a BARE `python3 -m pytest` of
`3246 passed, 2 skipped, 3 warnings` with ZERO failures. The probe was reverted and `git status` is
clean; this review commits no source change.

WHAT NEEDED CORRECTING WAS THE EXECUTION GUIDANCE, NOT THE DESIGN.

**E-01 TOLD THE EXECUTOR TO REUSE A HELPER THAT CANNOT EXPRESS ANY OF THESE TESTS (PR-901, HIGH).**
E-01 said to "REUSE THAT FILE'S EXISTING MACHINERY rather than inventing a fixture", naming the
`temp_git_repo` fixture and the `_run_group` helper. The fixture is fine. The helper is not:
`_run_group(artifact_type, setid, repo_dir)` hardcodes the selector `"zzzzzz"`, passes NO `--apply`,
and accepts NO `--order`, so it cannot run a single case this plan specifies. Worse, the file's whole
existing purpose is setid-LENGTH policy and it DEPENDS on `zzzzzz` matching nothing (two tests assert
`"zzzzzz" in out` as proof that resolution failed), so no test there has ever seeded a record
(`grep -n "notes.md\|write_text\|FRONTMATTER"` returns nothing). An executor following the instruction
would either widen a helper shared by three backend-parameterized tests it does not own, or discover
mid-task that the instruction was wrong. FIXED: E-01 now says the fixture is reusable and the helper is
not, says to write a new one beside it, explains why not to widen `_run_group`, and carries the two
seeding details review had to discover (`order` must be a QUOTED two-digit string because
`research_contract._ORDER_RE` is `\A\d{2}\Z` against a `str`, and records must sit under
`.aw/records/research/` for `--dir` to resolve them).

**THE `aw research set-assign` SPELLING WAS UNCOVERED BY ANY TEST (PR-905, MEDIUM).** The plan's Scope
and F-07 both correctly state that two spellings share one backend, and E-05 correctly fixes that
spelling's help string, yet every case in E-01 and E-04 drives only `aw group research`. Measured:
`cli.main(["research","set-assign","aaaaaa","--set","ns","--apply"])` on a `-03-` record also yields
`-00-` at exit 0. No extra production change is owed, because E-02 fixes both paths at once, but the
absence of a test means a later refactor giving `set-assign` its own path would regress this silently.
FIXED: added as F-12, as a required case in E-04, and as required evidence in V-04.

**E-03 ASKED FOR A FIX TO A PATH THAT NEEDS NONE (PR-902, MEDIUM).** E-03 was framed as "FIX THE
PREVIEW PATH", with the negative finding as an afterthought. Measured under the applied fix: the dry run
printed `-> 20260929-ns-03-...` and `-> 20260929-ns-07-...` and the `--apply` run produced those same
names, because `_apply_renames` prints `p.new_path.name`, the planned name. Unlike its plans-side twin,
which `e3hzyc` records as having printed the loop index, this preview was never wrong. Leaving the item
framed as a fix invites an executor to edit working code to satisfy it. FIXED: reframed as a
verification whose expected outcome IS the negative finding, with an instruction to stop and explain if
an edit seems necessary, and V-03 updated to match.

**THREE EDITS AND A LATENT TYPE HAZARD ARE NOW PINNED (PR-903, MEDIUM).** E-02 correctly warned that
`parsed.order` is a two-digit STRING while the explicit branch is an int, but left the resolution to the
executor ("convert deliberately"). The correct answer is to pass the string THROUGH unchanged, since
`research_contract.ResearchName` declares `order: str  # NN, two digits` and `format_name` interpolates
it directly; coercing to `int` and re-formatting adds a way to lose a leading zero for no gain. FIXED:
E-02 now records the exact three edits, that `Optional` is already imported so no import edit is needed,
that `parsed.order` passes through as a string, and the measured post-fix behavior.

**A DRIFTED BASELINE COUNT WAS STATED AS A BAR (PR-904, MEDIUM).** F-09 recorded `3202 passed, 2
skipped` and `## Required tests` told the executor the delta must be measured "against the `3202 passed,
2 skipped` baseline". Review measured `3246 passed, 2 skipped` on a clean tree at this HEAD. Both are
honest measurements of a clean tree; only the total drifted. FIXED in F-09 and in both places that cited
it: the bar is now zero failures plus a delta of exactly the new cases against the executor's own
freshly measured baseline.

Everything else in this plan verified as written and needed no change, including all three open
questions (each resolved from evidence with a correct rationale), the six deferral rows and their
carriers (`f7a2kc`, `j84jg3` both `open`; the `k9awrq` Carrier-Evidence path resolves), the
spec-sync section, and the scope fence. `aw check plans` reports zero findings for this plan. The
`[blocking]` glyph in the lint line is the inherited `- Blocks-Release: next` release gate, correct for
a `bug` per the every-live-bug-gates-the-release rule, and NOT an open blocking question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | E. Testing; G. Executability | `_run_group(artifact_type, setid, repo_dir)` hardcodes selector `"zzzzzz"`, no `--apply`, no `--order`; two existing tests assert `"zzzzzz" in out`; `grep -n "notes.md\|write_text\|FRONTMATTER" tests/test_group_verb_policy.py` returns nothing | E-01 instructed the executor to reuse a helper that cannot express any case this plan needs, in a file that has never seeded a record and whose tests depend on the selector matching nothing. Following it means either widening a helper shared by three backend-parameterized tests, or discovering the instruction is wrong mid-task. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now distinguishes the reusable fixture from the unusable helper, requires a new helper beside it, and carries the two measured seeding details (quoted two-digit `order`, records under `.aw/records/research/`). |
| PR-902 | MEDIUM | IN-SCOPE | E. Testing | Under the applied fix, the dry run printed `-> 20260929-ns-03-...`/`-> 20260929-ns-07-...` and `--apply` produced the same names; `_apply_renames` prints `p.new_path.name` | E-03 was framed as "FIX THE PREVIEW PATH" when the research preview derives wholly from planned names and is already correct, unlike the plans-side twin. As framed it invites editing working code to satisfy the item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reframed as a verification whose expected outcome is the negative finding, with a stop-and-explain clause if an edit seems needed; V-03 updated to match. |
| PR-903 | MEDIUM | IN-SCOPE | A. Correctness | `research_contract.ResearchName` declares `order: str  # NN, two digits`; `format_name` interpolates it directly; the three-edit fix measured green (`3246 passed, 2 skipped`) | E-02 flagged the string-versus-int hazard but left it to the executor to "convert deliberately", where the correct action is to pass the string through unchanged; coercing to int risks losing a leading zero for no gain. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 records the exact three edits, that `Optional` is already imported, that `parsed.order` passes through as a string, and the measured post-fix behavior. |
| PR-904 | MEDIUM | IN-SCOPE | E. Testing | Authoring `3202 passed, 2 skipped`; review `3246 passed, 2 skipped, 3 warnings` on a clean tree at HEAD `77c9ae12`, zero failures both times | A drifted absolute suite total was stated as the comparison bar, so normal drift would read as a finding. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 and both citing passages now require the executor's own freshly measured baseline; the bar is zero failures plus the new-case delta. |
| PR-905 | MEDIUM | UNDER-SCOPE | E. Testing | `cli.main(["research","set-assign","aaaaaa","--set","ns","--apply","--dir",repo])` on a `-03-` seed yields `20260929-ns-00-aaaaaa-a.notes.md`; both spellings reach `research_refs.run_set_assign` | The second CLI spelling carries the identical defect, and E-02 fixes it, but no E- or V-item exercised it, so a later refactor giving `set-assign` its own path would regress it silently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12, a required E-04 case, and required V-04 evidence that the case fails before E-02 and passes after. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Is the plan's filename-only tier decision (rejecting the backlog item's front-matter-first recommendation) correct? | YES, endorsed, and made falsifiable | Front-matter-first as the item recommends, rejected because the verb itself leaves frontmatter stale; asking the maintainer, rejected because the repository answers it by measurement | Reproduced the exact corrupt state in one probe: names read `-00-`/`-01-` while frontmatter read `order: "03"`/`order: "07"`. `f7a2kc` is still `open`. `research_refs.plan_mv` already trusts the filename tier | yes |
| D-2 | E-01 names a helper that cannot express the tests. Rewrite the instruction, or widen the helper? | Rewrite the instruction to require a NEW helper | Widening `_run_group`, rejected because its three callers are parameterized over every backend in `GROUP_TYPES`, so this plan would take ownership of tests outside its concern and could perturb unrelated backends | `_run_group`'s signature and its `"zzzzzz"` literal; the three `@pytest.mark.parametrize("artifact_type", GROUP_TYPES)` callers; the file seeds no records anywhere | yes |
| D-3 | The `set-assign` spelling is untested. Add a test, or widen production scope? | Add a test only | Adding a production change for `set-assign`, rejected as unnecessary since both spellings already dispatch to the one backend E-02 fixes, so a second change would be duplicate logic | `artifact_types.TYPE_BACKENDS["research"]["group"] == "research_refs.run_set_assign"`; the measured `-00-` clobber through the `set-assign` spelling | yes |
| D-4 | Does the plan need a spec amendment? | No | Amending `agents-artifact-organization`, rejected because the plan moves the code TOWARD what that spec already says rather than changing the contract | Section 5.6 specifies what the verb does without fixing which `NN` an absent flag assigns; the `<NN>` bullet and Section 5.8 both reserve `00`; the group verb row marks `--order` optional | yes |

No `Reversible: no` decision was taken, so no escalation is owed. No finding was left `OPEN` or
`DEFERRED`, so no `- Blocking: yes` escalation question is owed under the gate threshold.
