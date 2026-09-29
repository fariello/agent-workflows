# Review findings: plan 3pwpq1

- Subject-Id: 3pwpq1
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f0186892` in a lane worktree. Structural preflight `aw ipd lint --phase author`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms after
revision. No pre-review snapshot was owed: the plan was committed and unmodified (`git status
--short` empty at review start). NO PRODUCTION FILE WAS MODIFIED: every measurement came from
read-only probes and throwaway `git init` repos under the gitignored `.aw/state/`, all removed
afterwards.

THE PLAN'S CORE DIAGNOSIS IS CORRECT AND REPRODUCED EXACTLY. F-01's 308 previewed against 358
applied, a 50-path apply-only difference and an EMPTY preview-only difference, all reproduce at this
head, so the defect is pure omission. F-02's structural cause is confirmed by reading `engine.run`'s
`if plan.diff:` block ending in `continue` before `ensure_repo_root`. F-05's zero-byte trap
reproduces (`''.join([]) == ''.join([])` is `True`, `difflib.unified_diff([], [])` is `[]`, 22 of the
in-scope paths are `.gitkeep`). F-06 reproduces (`install --diff` exits `unrecognized arguments`).
F-07 reproduces (`19313eed` deleted both parity modules; neither exists at HEAD). F-09 reproduces
(an already-installed repo previews `No changes (everything is already current).`). F-10's inlined
duplicate block is where the plan says it is. This was a careful, well-evidenced plan.

WHAT REVIEW FOUND IS THAT EXECUTING IT AS WRITTEN WOULD HAVE SHIPPED A WORSE DEFECT THAN THE ONE IT
FIXES. There is a single root cause with two measured consequences, and it is why this review is not
a rubber stamp.

**THE PREVIEW WOULD HAVE CLAIMED AN INSTALL OVERWRITES THE USER'S OWN FILES (PR-001, BLOCKER).**
The plan's whole design rests on OQ-02's conclusion that the existing renderer implements
"propose when absent, omit when present" for free, because it skips any member whose content matches
the destination. It does not. It implements "omit when IDENTICAL", and the difference is the entire
population the no-clobber rule exists for. All 20 non-empty in-scope paths are written only when
absent, so a user's own copy survives forever; but `show_install_diffs` renders a proposed member
against whatever is on disk, with no notion of write policy. Measured on a throwaway repo installed
and then customized the way a real target repo is (a plans README, a specs README, the comms README,
`.gitleaksignore`, the secret-scan workflow, and two own `.aw/.gitignore` lines): the unfiltered
design printed 6 `Diff:` headers and 10 red `-` removal lines, including
`-# Our team's plan conventions`, `-# Our specs index`, `-# Our comms policy`,
`-name: our secret scan` and `-# team rule`, while a real apply into that same repo changed NOTHING
(`diff -rq` against a pre-apply snapshot, empty). An operator shown a diff that promises to delete
their files would reasonably cancel the install, so this is a worse failure mode than the silent
omission: it converts a quiet wrong answer into a loud one. Fixed by a new E-07 that filters
only-when-absent members on destination existence at the preview boundary, on the same predicate
`create_setup_artifacts`' own dry-run branch already uses; verified that with the filter the same
customized repo previews `No changes (everything is already current).`, which is what the apply does.
E-07 is placed at the boundary and NOT in the renderer, because body and generated members are
overwrite-semantics members whose diffs are the installer's primary output; V-07 and E-06 property
(8) both require a modified body member to still diff, so a filter applied too widely fails too.

**`.aw/.gitignore` IS NOT A FLAT MEMBER AND WOULD HAVE MISREPORTED TOO (PR-002, HIGH).** Authoring
counted it in the declarative 43 because `create_setup_artifacts` hands it to `_create_if_absent`.
But `_ensure_aw_gitignore` also runs on the same install (traced live:
`install_into_repo` -> `create_setup_artifacts` -> `migrate_local_lanes_to_untracked` ->
`_ensure_aw_gitignore`) and APPENDS every missing pattern to an existing file, so on an
already-installed repo the content is the union of the user's lines and the framework's patterns in
the user's order. Two probes: a repo with its own two lines previewed `-# MY OWN RULE` / `-scratch/`
against an apply that changed the file not at all; and a repo simulating an older install (with
`/inbox/` removed mid-file) shows the back-fill appending it at the END, so a template diff reports a
spurious move (`+/inbox/` at line 25, `-/inbox/` at the end) for a file the back-fill has already
made correct. Excluded from the map with its own deferral entry and carrier, and the class split
corrected from four classes at 43 / 2 / 2 / 3 to five at 42 / 1 / 2 / 2 / 3 throughout.

**RETIRING THE INLINE BLOCK RETIRES A GUARD, NOT ONLY A DUPLICATE READ (PR-003, HIGH).** E-03
described the `.aw/workflow-artifacts/README.md` retirement purely as removing a duplicated template
read and fallback. That block is wrapped in `if not artifacts_dest.is_file():`, making it the one
existing, working instance of the rule PR-001 shows is mandatory. Measured: moving that member onto
an unfiltered map makes the preview print `Diff: .aw/workflow-artifacts/README.md` against a repo
whose copy the user customized, where today it prints nothing. E-03 now states that the guard is
replaced generically by E-07 and must not be landed without it; V-03 requires the customized-repo
evidence.

**THREE EVIDENCE CORRECTIONS (PR-004 MEDIUM, PR-005 MEDIUM, PR-006 LOW).** `--dry-run` names 45 of
the 50, not 47: the two `emit_layout_artifacts` paths are also missing, because `install_into_repo`
never surfaces the returned `layout_artifacts` in its printed summary even though
`emit_layout_artifacts` honors `dry_run` and returns them. No decision moves (those paths were
already out of scope) but the fallback F-08 offers operators is weaker than claimed, and the carrier
note now records the cheaper half of that fix. Separately, E-04's renderer change needed a
collateral-damage check that the plan never specified, since the renderer is shared: measured zero
zero-length members among the 159 body members, the shim map and the skill map, so no existing
member's rendering can change; that census is now required evidence in V-04 rather than an assumption.
And the arithmetic of the zero-byte trap was off by one in the plan's favor (closing 21 of 43 should
read 20 of 42).

Every finding is FIXED. None was deferred, so no escalation to a `- Blocking: yes` question is owed.
The plan's two pre-existing non-blocking open questions survive with corrections: OQ-01's answer
(the shared declarative map) is UNCHANGED and is if anything strengthened, since PR-003 shows the one
duplicated model in the renderer was also the one carrying a guard worth keeping; OQ-02's answer is
unchanged in words but its reasoning was falsified and rewritten, because the renderer does not
implement it for free in either direction. OQ-03 (the merge-writer paths) is untouched and correctly
deferred. A new deferral entry carries `.aw/.gitignore`.

The plan's structural quality is otherwise high and review left it alone: the E/V bijection is real,
V-items demand pasted paths rather than counts, E-01 re-derives its own baseline rather than
asserting the authored figure, the scope fence declares no stop-on-scope directive, and the gate
carries the honesty rule, the path-scoped commit obligation and the conditional finalize ownership.
E-06's insistence on no module-level slow mark is well-founded: the only surviving `--diff` test sits
in a `pytestmark = pytest.mark.slow` module, which is why `addopts`' `-m 'not slow'` let this defect
live.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | blocker | UNDER-SCOPE | A. Correctness and data integrity | `agent_workflows/engine.py` `show_install_diffs` (the `if "".join(current_lines) == "".join(new_lines): continue` skip); plan OQ-02; review probe on a customized throwaway repo | The 20 non-empty in-scope paths are NO-CLOBBER, but the renderer diffs proposed content against whatever is on disk. Unfiltered, the preview prints a destructive diff against a user's customized scaffolding: 6 false `Diff:` headers and 10 `-` removal lines quoting the user's own content, measured against an apply that changed nothing. Worse than the omission being fixed, because an operator reads it and cancels. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | New E-07 filters only-when-absent members on destination existence at the preview boundary (same predicate as `create_setup_artifacts`' dry-run branch); new V-07 demands the falsifying probe with quoted strings plus a modified-body-member counter-case; new F-11; E-06 gains properties (7) and (8) and a third mutation; Goal, Scope, Concern and gate all updated. |
| PR-002 | high | IN-SCOPE | D. Anti-regression and domain invariants | `agent_workflows/engine.py` `_ensure_aw_gitignore`; traced call chain `install_into_repo` -> `create_setup_artifacts` -> `migrate_local_lanes_to_untracked` -> `_ensure_aw_gitignore`; two review probes | `.aw/.gitignore` was counted declarative, but the same install APPENDS missing patterns to an existing file, so its installed content is not the template. Offering it as a flat member previews the user's own lines as removals, and on a back-filled repo previews a spurious mid-file move. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Excluded from the producer in E-02 with the measured reason; new F-12; new deferral entry with carrier `9vkhkk`; class split corrected to 42 / 1 / 2 / 2 / 3 in F-03, E-01, V-01, V-05, the scope check and the gate. |
| PR-003 | high | IN-SCOPE | C. Architecture and operability | `agent_workflows/engine.py` `show_install_diffs`, the `if not artifacts_dest.is_file():` wrapper around the `artifacts_readme` block; review probe | E-03 framed the inline-block retirement as removing a duplicated template read, but the block also carries the only existing instance of the existence guard PR-001 requires. Retiring it onto an unfiltered map DELETES that guard; measured, the preview then prints a header for a customized artifacts README where today it prints none. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-03 now states the guard is replaced generically by E-07 and must not land without it; V-03 requires customized-repo evidence for that path; F-10 records the wrapper. |
| PR-004 | medium | IN-SCOPE | E. Testing and verification | `agent_workflows/engine.py` `emit_layout_artifacts` (honors `dry_run`, returns paths) against `install_into_repo`'s summary, which never surfaces `layout_artifacts`; per-path membership test of the 50 against a `--dry-run` log | F-08 claimed `--dry-run` names 47 of 50 with only the 3 bookkeeping paths missing. It names 45: the two `emit_layout_artifacts` paths are absent from both dry surfaces because the returned list is never printed. The operator fallback F-08 offers is weaker than stated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-08 rewritten with 45 / 5 and the mechanism; the layout deferral entry records that the summary omission is the cheaper half for the carrier. |
| PR-005 | medium | UNDER-SCOPE | D. Anti-regression and domain invariants | review probe over `collect_source_members` (159 members), `generate_shim_members`, `_build_skill_members` | E-04 changes a SHARED renderer's absence decision but the plan required no check that no existing member is affected. Measured: zero zero-length members in all three producers, so E-04 is safe, but the plan asserted safety only for the scaffolding it was adding. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-04 now requires the census to be re-derived at the executing head; V-04 requires it pasted and fails the item on a nonzero count; new F-13, which also records why the E-07 filter must NOT reach body members. |
| PR-006 | low | IN-SCOPE | Evidence accuracy | plan F-05 and the authoring history note ("closes 21 of 43") | With 22 zero-byte paths, merging without E-04 closes 20 of 42, not 21 of 43. A one-off arithmetic slip in the plan's own favor, in the sentence that exists to warn against a plausible-looking partial success. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Corrected to 20 of 42 in F-05, OQ-02, E-04 and the history note; F-05 also now names F-11 as the opposite-direction trap on the same conflation. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan would preview a destructive diff against user-customized no-clobber files. Raise it as a blocking question for the maintainer, or fix the design in place with a new E-item? | Fix in place: add E-07 (existence filter at the preview boundary) and V-07, and rewrite OQ-02's reasoning. | (a) Raise as `- Blocking: yes`: rejected because the repository answers it decisively. The apply path already contains the exact predicate (`if not (repo_root / rel).exists()` in `create_setup_artifacts`' dry-run branch) and the renderer already contains a working instance of the rule (`if not artifacts_dest.is_file():`), so this is a mechanism question resolvable from evidence, not a maintainer judgement about scope or risk appetite. (b) REPLAN: rejected as disproportionate; the plan's shared-map architecture is sound and the gap is one filter plus one test property. | Probe: unfiltered preview on a customized repo -> 6 `Diff:` headers and 10 `-` lines quoting the user's content; `diff -rq` after a real apply into the same repo -> empty; with the filter -> `No changes (everything is already current).` | yes |
| D-2 | Where does the existence filter belong: in the producer, in the renderer, or at the preview composition boundary? | At the preview composition boundary (E-05's call site), applied to the scaffolding map alone. | (a) In the producer: rejected because the rewired apply-path ensurers consume the same map, and a pre-filtered map would silently change what they iterate. (b) In the renderer: rejected as actively harmful, since `show_install_diffs` also receives the 159 body members plus the generated maps, which are OVERWRITE-semantics members whose diffs against existing files are the installer's primary output; an existence filter there would stop reporting every framework file update. | `install_all` writing body members over existing files; `_create_if_absent` and the `is_file()` guards filtering per target on the apply path; E-06 property (8) and V-07's counter-case are the falsifiers for the over-wide variant. | yes |
| D-3 | Is `.aw/.gitignore` a declarative member (as authoring classified it) or not? | Not a member; excluded and deferred with carrier `9vkhkk`. | (a) Keep it in the map: rejected on measurement, since the preview then shows the user's own lines as removals and shows a spurious move on a back-filled repo. (b) Model the append in the map: rejected as the same feature the two merge-writer paths need, which OQ-03 already defers as a distinct piece of work; adding it here would widen this plan into merge-result previewing. | Traced call chain to `_ensure_aw_gitignore`; probe 1 (`-# MY OWN RULE` / `-scratch/` against a no-op apply); probe 2 (`+/inbox/` line 25 with `-/inbox/` at the end after a back-fill). | yes |
| D-4 | E-07 is a new item executed third but numbered last. Renumber the checklist so reading order matches id order, or keep ids monotonic? | Keep ids monotonic (E-07 allocated after E-06, `Highest E allocated: 07`) and make the ordering machine-checked by having E-04 declare `Depends on: E-07`. | Renumber E-04/E-05/E-06 upward to insert E-07 in sequence: rejected because the plan's own history, findings and gate already cite those ids, and renumbering would invalidate every cross-reference while a dependency edge expresses the same ordering unambiguously. | `aw ipd lint` validating `Depends on` edges (it rejected the interim `E-03a` spelling and the missing-target edge) and reporting `conforming` with the final numbering; the plan's `- Highest E allocated:` field being a monotonic allocator. | yes |
