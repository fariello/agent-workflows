# Review findings: plan lmyeas

- Subject-Id: lmyeas
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a52968550`. The plan file was committed and clean
(`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, ZERO findings) BEFORE semantic
review. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator
child-row check does not apply. The declared dependency is satisfied: `bjgqez` resolves to
`.aw/records/plans/executed/20260929-ci9kx2-01-bjgqez-...ipd.md`, so E-03's branch is reachable and
V-03's BEFORE column will measure the refusal rather than the old silent behavior.

I DROVE THE BEHAVIOR RATHER THAN READING THE PLAN, and that is what produced the three findings that
matter. The plan's central DECISION is sound and survives review intact: an explicit `--dir` must not
climb. I reproduced every load-bearing argument for it. What did not survive is the plan's
characterization of the DEFECT (it is worse than "unhelpful"), its claim about test coverage (already
covered), and its suite baseline (stale).

WHAT REPRODUCES EXACTLY:

- F-01 reproduces end to end on a seeded temp project with `cwd` outside any AW project:
  `attention --dir <root>` gives `1 artifact shown` at exit 0, `attention --dir <root>/src/deep`
  gives exit 3, and a BARE `attention` from inside `src/deep` climbs and gives `1 artifact shown` at
  exit 0. The explicit form is the only one that gets the wrong answer. (Post-`bjgqez` it now refuses
  rather than printing `0 artifacts shown`, exactly as the plan says.)
- F-02 reproduces. `is_project_dir(<root>/src/deep)` is `False` while
  `find_project_root(<root>/src/deep)` returns `<root>`; for an unrelated directory the pair is
  `False` / `None`. The conflation is real and E-01's classifier is the right shape for it.
- F-05 reproduces by reading the module: `run_archive` calls
  `repo_root = resolve_verb_repo_root(getattr(args, "dir", None))`, and the delete helper's body is
  `shutil.rmtree(target, ignore_errors=False)` guarded only by `rel == Path(".")` and a
  `relative_to` ValueError, both computed RELATIVE to the resolved root. Neither guard protects
  against the root being the wrong repository. This is the strongest single argument in the plan.
- F-06 reproduces on this machine: `is_project_dir(os.path.expanduser("~"))` is `True`, and `~/.aw`
  holds `config`, `projects` and `state`, so one durable child is enough for `_is_project_marker`.
- F-07 reproduces by walking this lane's ancestry: the lane itself is a project root, `.aw/worktrees`
  and `.aw` are both `False`, and the next `True` is the SHARED CHECKOUT, with `$HOME` after it. The
  lane-ancestry hazard is exactly as described.
- F-08 reproduces. `backlog new --dir <subdir>` without `--apply` prints
  `--- would write <subdir>/.agents/backlog/open/...backlog.md ---`, a visibly wrong path that
  writes nothing. Loud and local, as the plan argues.
- F-09 reproduces. `cli._run_install` reads `args.targets` positionally with a cwd default;
  `doctor.run` resolves its own `Path(getattr(args, "dir", None) or os.getcwd())` and bypasses the
  resolver entirely.
- F-10 reproduces. `backlog.run_set` does `gate_root = resolve_verb_repo_root(gate_dir_arg)` then
  `if not is_project_dir(gate_root):` and refuses with
  `--gate-dir '<x>' is not an agent-workflows project root`. Resolve-verbatim-then-fail-closed.
- F-11 reproduces. `no_project_message`'s git tail is the quoted
  `{git_root} IS a git repository, but agent-workflows is not installed in it.` plus
  `Install it there with: aw install {git_root}`, and `git_root_for_message` exists for the machine
  side. The precedent the plan cites is real, which is what makes PR-001 so sharp.
- F-12 reproduces. `grep -rln resolve_verb_repo_root .aw/records/specs/ docs/` returns NOTHING, so
  the docstring genuinely is the only contract document and E-02 is the right place for the decision.

THE THREE FINDINGS THAT CHANGE THE WORK:

PR-001 is a BLOCKER and it inverts the plan's framing of its own deliverable. The plan says the
refusal is "correct-but-unhelpful" and that E-03 should "upgrade" it by naming the root. Driven on a
seeded project where agent-workflows IS installed at `<root>`, the refusal for
`--dir <root>/src/deep` ends:

    /tmp/.../proj IS a git repository, but agent-workflows is not installed in it.
    Install it there with: aw install /tmp/.../proj

while `(root/".aw"/"system").is_dir()`, `(root/".aw"/"records").is_dir()` and
`is_project_dir(root)` are all `True`. The `--agent` surface emits
`{"outcome":"cannot-run","exit":2,"next":"aw install ."}`. So the refusal is not merely unhelpful, it
states a FALSEHOOD and offers a remedy that acts on it: an operator or agent following the printed
instruction runs an install against an already-installed project. The mechanism is that both
branches are gated only on a git root existing (`_find_git_root(where) is not None` in
`no_project_message`, `git_root_for_message(repo_root) is not None` in `attention.run`) and neither
asks whether that git root is already an AW project; the branch was written for the "real repo, no AW
installed" case in `quqyc4` and this input falls into it. Had the plan executed as written, E-03
would have added a helpful root-naming line DIRECTLY ABOVE a sentence contradicting it, and E-04's
assertions would all have passed. Fixed by rewriting E-03 to REPLACE the false sentence and the offer
on the inside-a-project branch (leaving it intact for the no-AW-project git case where it is true),
requiring the machine `next` to stop being `aw install .` (with `next: null` named as an acceptable
honest answer), adding the negatives to E-04 and V-03, requiring the BEFORE column to paste the false
sentence verbatim, and recording it as F-14.

PR-002 is a HIGH on a false premise that would have produced duplicated work. E-04 states the
subdirectory case is one "no existing test reaches" and that surviving coverage "calls
`attention.run` in process with `dir=None`". Both are wrong. `tests/test_explicit_dir_non_project.py`
is a 13-test subprocess-driving file whose
`test_real_project_root_control_and_subdirectory_refusal` already builds a real project with an open
backlog item AND a `src/deep` subdirectory and asserts `--dir <root>` -> `1 artifact shown` at 0,
`--dir <subdir>` -> exit 3 with the verbatim-no-climb sentence, `--agent` -> exit 2 `cannot-run`, and
`run_cwd=self.deep_subdir` bare -> climbs to `1 artifact shown` at 0. Those are precisely this plan's
"three controls" plus its subdirectory case. `test_no_dir_controls` and
`test_machine_summary_content_and_path_free` cover the rest. So E-04 as written would have
re-asserted about four shipped assertions while leaving the PR-001 negatives unpinned, which is the
only genuinely uncovered surface. Fixed by correcting the premise in E-04, redirecting it onto the
classifier plus the F-14 negatives, requiring it to cite which existing test owns each case and to
paste that file's run as control evidence rather than duplicating it, and recording F-15.

PR-003 is a HIGH because a stale baseline makes an executor misjudge its own run. F-13 instructs the
executor to expect `1 failed, 3427 passed, 2 skipped` and to treat
`test_release_exempt_setter_roundtrip_and_parity` as a known failure. Re-measured on a clean tree:
`3665 passed, 2 skipped, 3 warnings in 76.90s`, fully green, and that test passes in isolation
(`1 passed in 0.21s`). The underlying clock split is real and unchanged (`backlog.py` uses
`datetime.date.today()`, `status_set.py` uses a UTC `datetime.now(timezone.utc)`), but the skew
window was closed at review (`date` and `date -u` both 2026-10-01). An executor told to expect a
failure could read a green run as anomalous, or worse, could see this test fail during a skew window
and have no instruction to check the clock. Fixed by rewriting F-13 with both measurements, changing
the bar to "no new failing node ids against a baseline you measure yourself", and telling the
executor to compare `date` with `date -u` before calling it a regression.

PR-004 and PR-005 are measurement drift. The resolver census has now moved three times: the docstring
says 64/21, the plan says 78/24 raw with 37 AST invocations across 22, and review measures 88/26 raw
with 44 invocations across 24. The direction of the write-class argument is unaffected, but E-02 was
instructing the executor to write this plan's figure into the docstring, which would be stale on
arrival; it now must write its own dated measurement, and F-16 records why. Separately F-03's
measurements reproduce AND extend: `aw check --dir <subdir>` reports `✓ CONFORMS  0 all checked`
where `--dir <root>` reports `4 all checked`, which the plan did not record and which is arguably the
worst surface in the set since `aw check` is what CI runs. Added to F-03, to the scope check as
accepted under-scope, and to the scope fence as an explicit do-not-convert.

PR-006 is a process note worth keeping: review's FIRST probe seeded no artifact and so measured
`0 artifacts shown` at the project ROOT, which would have "confirmed" nothing. The plan's own E-04
already requires a seeded fixture; I added the same requirement to the Required-tests matrix and to
V-03, because the before/after matrix is where a vacuous fixture would silently pass.

ON THE DECISION ITSELF (OQ-01). I considered overruling it and did not. The read-only carve-out is
the only coherent alternative, and F-04's point that several helpers serve read and write verbs
through one call site is correct, so the carve-out cannot even be expressed before those helpers are
split. Combined with the measured `shutil.rmtree` site and `$HOME` being a project root, refusing is
the right default and the remaining defect (an unexplained, and as it turns out false, refusal) is
fully fixable without touching resolution. OQ-01 is `Status: resolved`, `Owner: executor`, which is
the correct attribution for a reviewer-or-author decision, and the approval gate surfaces it for a
maintainer to overrule.

ON RIGHT-SIZING. Four E-items in three groups. E-03 grew at review (it now corrects a falsehood as
well as adding a diagnostic) and I considered splitting the correction from the root-naming. I did
not: they touch the same two branches in the same two files, a split would leave one commit shipping
a self-contradicting message, and V-03 verifies both in one evidence pass. E-01 is a pure predicate,
E-02 is docstring-only with an explicit body-unchanged check, E-04 is one test file. No split
recommended.

ON THE EXECUTION CONTRACT. The gate already carries resolved questions, a declaration-style scope
fence with no prohibited "STOP and report" clause for the out-of-scope case (it correctly says make
the edit and justify it with `--scope-reason`), the paste-the-actual-output honesty rule, path-scoped
`aw commit` with never-push, and a correctly CONDITIONAL finalize-ownership paragraph naming
`AW-LIFECYCLE-ROLE-001`. It also correctly states that `5gmi12` reaches `done` only on execution so
the `Blocks-Release: next` gate survives the handoff. I added two prohibitions to the fence (do not
convert the other validators; do not change the git tail for the case where it is true) and nothing
else.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | F. Prevent silent failure / honest documentation | `agent_workflows/project_context.py:403` (`f"\n{git_root} IS a git repository, but agent-workflows is not installed in it.\n"`); `agent_workflows/attention.py:3963` (`git_root = git_root_for_message(repo_root)`) | For `--dir <subdir of an INSTALLED project>` both surfaces assert a FALSEHOOD and offer a wrong remedy: the human message says agent-workflows "is not installed in it" and offers `aw install <root>` for a root where it IS installed; the machine record sets `next: "aw install ."`. Both branches gate only on a git root existing and never ask whether it is already an AW project. The plan framed the refusal as merely unhelpful, so E-03 as written would have added a helpful line directly above a contradicting sentence and E-04 would still have passed. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 rewritten to REPLACE the false sentence and the install offer on the inside-a-project branch only (the no-AW-project git case keeps it, where it is true) and to stop `next` being `aw install .`; E-04 and V-03 must assert the negatives; the BEFORE column must paste the false sentence; recorded as F-14; Goal, Scope and the approval gate updated. |
| PR-002 | HIGH | IN-SCOPE | E. Testing and verification | `tests/test_explicit_dir_non_project.py:236` (`def test_real_project_root_control_and_subdirectory_refusal`), `:247` (`["attention", "--dir", str(self.deep_subdir)]`), `:266` (`run_cwd=self.deep_subdir`) | E-04's premise that the subdirectory case is one "no existing test reaches" and that surviving coverage runs in process with `dir=None` is FALSE. The sibling's file drives the real CLI in a subprocess and already pins the subdirectory refusal, the `--agent` exit 2 and all three of this plan's controls. Acting on the premise duplicates roughly four shipped assertions while leaving the PR-001 negatives unpinned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04's premise corrected and the item redirected onto the classifier plus the F-14 negatives; it must cite which existing test owns each case and paste that file's run as control evidence instead of duplicating it; V-04 updated; recorded as F-15. |
| PR-003 | HIGH | IN-SCOPE | G. Plan executability (live-artifact criteria) | plan F-13 ("the baseline is `3427 passed` with that ONE known failure") | The suite baseline is stale and misdirects the executor. Re-measured clean: `3665 passed, 2 skipped, 3 warnings in 76.90s`, fully green, and the named test passes in isolation. The clock defect is real but its skew window was closed at review. An executor told to expect one known failure can misread a green run, or can see a genuine skew failure with no instruction to check the clock. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 rewritten with both measurements and the mechanism; the bar changed to no-new-failing-node-ids against a self-measured baseline; Required tests and V-04 now tell the executor to compare `date` with `date -u` before calling it a regression. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence accuracy (Step 1) | `grep -rn --include=*.py resolve_verb_repo_root agent_workflows/` = 88 lines / 26 modules; AST `ast.Call` census = 44 invocations / 24 modules | The resolver census has drifted a third time (docstring 64/21, plan 78/24 and 37 invocations, review 88/26 and 44). E-02 instructed the executor to write the plan's figure into the docstring, which would be stale on arrival. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and V-02 now require the executor's OWN dated measurement and explicitly forbid transcribing the plan's or review's numbers; the per-module census is recorded as F-16; the "37 call sites" phrasing in V-02 de-pinned. |
| PR-005 | MEDIUM | UNDER-SCOPE | F. Prevent silent failure | driven: `aw check --dir <subdir>` -> `✓ CONFORMS  0 all checked` at exit 0 vs `--dir <root>` -> `✓ CONFORMS  4 all checked` | F-03's systemic under-reporting extends to `aw check` itself, which the plan did not record. That is the surface a CI step is likeliest to call, so omitting it understates the carried work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to F-03's finding and evidence, recorded in Scope check as accepted under-scope belonging to carrier `rgl2d4`, and added to the scope fence as an explicit do-not-convert so an executor does not fix it on the way past. |
| PR-006 | LOW | IN-SCOPE | E. Testing and verification | plan Required tests, the before/after matrix row for the project ROOT control | The matrix did not require the project fixture to be seeded with a real artifact, so the ROOT control row can read `0 artifacts shown` and prove nothing. Review's first probe made exactly this mistake and had to be redone. (E-04 already required seeding; the matrix did not.) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Required-tests matrix and V-03 now require the fixture to be seeded via `aw backlog new ... --apply` and say why, naming review's own failed probe as the reason. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is correcting the false `not installed` claim within this plan's scope, or does it belong to a new plan or to `bjgqez`? | In scope for E-03, with no new scope path. | (a) File a separate plan or backlog item for the falsehood (rejected: it is emitted on the exact branch and for the exact input this plan exists to improve, so shipping the root-naming without it would produce a self-contradicting message); (b) treat it as `bjgqez`'s to fix (rejected: the git tail is pre-existing `quqyc4` behavior, not `bjgqez`'s, and `bjgqez` is already executed and unwritable). | The falsehood reproduces on the inside-a-project branch `attention.run` and `cli._run_plans` already guard; all three affected files are already in `- Scope-Paths:`; `AGENTS.md` forbids changing what an executed plan records. | yes |
| D-2 | Should E-03 also fix the git-root gate for inputs other than the inside-a-project case? | No. Fix only the branch where a defect reproduces; record that the gate's shape was examined. | Hardening `no_project_message` to ask `is_project_dir(git_root)` unconditionally (rejected as an unmeasured change: review found no reachable input that lands on the no-project branch while an AW project exists above the git root, since any path inside an installed project classifies as inside-a-project, which E-03 now handles). | Driven enumeration of the four input classes (root / subdir / non-project non-git / non-project git); only the subdir case reproduces the falsehood. Recorded as a Carrier-Declined entry stating no defect is asserted. | yes |
| D-3 | Should E-04 still create a new test file given that the subdirectory case is already covered? | Yes, but scoped to the classifier and the F-14 negatives, citing the existing file for the rest. | (a) Drop E-04 entirely (rejected: the classifier and the F-14 negatives are genuinely unpinned, and the negatives are what stop a root-naming-only implementation passing); (b) extend `tests/test_explicit_dir_non_project.py` in place (rejected: that file is `bjgqez`'s deliverable and is not in this plan's `- Scope-Paths:`, so extending it would be an undeclared out-of-scope edit). | `tests/test_explicit_dir_non_project.py`'s 13-test census and its subdirectory assertions; this plan's declared `- Scope-Paths:` names `tests/test_explicit_dir_subdir_resolution.py` only. | yes |
| D-4 | Does the plan's no-climb decision (OQ-01) warrant overruling at review? | No. Uphold it. | The read-only carve-out (rejected as not yet expressible: F-04's measurement that several helpers serve read AND write verbs through one call site means the helpers must be split first, which is strictly larger work; combined with the measured `shutil.rmtree` site and `$HOME` being a project root, refusing is the safe default and the residual defect is fully fixable without touching resolution). | `workflow_artifacts_prune.run_archive`'s `shutil.rmtree(target, ignore_errors=False)` with root-relative guards; `is_project_dir(~)` True; the lane ancestry walk reaching the shared checkout; `backlog.run_set`'s shipped resolve-then-fail-closed precedent. | yes |
