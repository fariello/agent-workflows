# Review findings: plan 3qxuw1

- Subject-Id: 3qxuw1
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a2c6915a` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after. No pre-review snapshot was owed: `git status --porcelain` was empty, so the plan was
committed and unmodified. No production file was modified; the derivation was prototyped as a
throwaway probe module that monkeypatched nothing in place and was deleted, with `git status
--porcelain` empty again afterwards.

ALL THIRTEEN AUTHORED FINDINGS WERE INDEPENDENTLY REPRODUCED AND ALL THIRTEEN HOLD. F-01:
`check_engine._identity_rename_hint('roadmaps','7ny1bg','Id',False)` returns `aw rename research
7ny1bg --to-id6 --apply` and running `aw rename research 7ny1bg --to-id6` exits 2 with `no research
artifact matched '7ny1bg'`. F-02: `artifact_types.TYPE_BACKENDS['roadmaps']['rename']` is
`artifact_rename.run_rename_roadmaps`, and `aw rename roadmaps 7ny1bg --slug x` exits 0 previewing the
rename plus exactly 4 citation rewrites in 2 `backlog/done/` records, matching F-09's count. F-03: the
two nouns are genuinely opposite (`resolve(roadmaps,'effzzi')` 0 paths versus `resolve(research,'effzzi')`
1 path; `resolve(roadmaps,'7ny1bg')` 1 path versus `resolve(research,'7ny1bg')` 0 paths). F-04:
`check_name_identity(repo, include_retired=True)` yields 11 findings, NONE on a `.roadmap.md` or under
`.aw/records/roadmaps/`, so the branch's population really is zero. F-05: three `.roadmap.md` files
exist at the three paths named, so the comment's flat claim is false for one of them. F-06:
`status_set.detect_artifact_type` returns `roadmaps` for ALL THREE files, including the two only
`research` resolves. F-08: both files parse as research with `kind='roadmap'`
(`set=awoptimize id=effzzi`, `set=7ny1bg id=7ny1bg`). F-11: `to_id6` appears 0 times in
`plans_refs.py`. F-13: no test executes an emitted command.

THE CENTRAL DESIGN DECISION IS CORRECT AND WAS PROVEN, NOT JUST CHECKED. Review implemented E-02's
containment derivation (over `_IDENT_RENAME_TYPE`'s own key set, using `selectors.record_dirs`) and it
returns `roadmaps` for the `roadmaps/`-tree file and `research` for both research-tree `.roadmap.md`
files. Every derived command then RUNS: `aw rename roadmaps 7ny1bg --to-id6`, `aw rename research
effzzi --to-id6` and `aw rename research 3rpcmu --to-id6` all exit 0. So the plan's answer to OQ-01 and
OQ-02 is right, its rejection of `detect_artifact_type` is measured rather than asserted, and its
correction of the backlog item's diagnosis is accurate.

This is a careful, honest, correctly-fenced plan. It states its own latency rather than inflating the
harm, it corrects the item that spawned it, it chose an executability oracle over string equality, and
its Deferred section carries five entries each with a real reason. Review found no fault with the
derivation, the fence, or the priority. What it found is that the plan addresses TWO of the helper's
THREE emitted shapes, and that one of its two prescribed fixtures cannot be built as described.

**THE HELPER EMITS `aw group` ON ONE BRANCH, THAT BRANCH IS EQUALLY BROKEN, AND THE PLAN'S TESTS
NEVER TOUCH IT (PR-701, HIGH).** `_identity_rename_hint` reads ONE `rename_type` and returns three
shapes from it: `aw rename <t> <sel> --to-id6 --apply` (legacy), `aw group <t> <sel> --set <setid>
--rename --apply` (modern plus `Set` field), and `aw rename <t> <sel> --slug <slug> --apply` (modern,
other field). The `roadmaps -> research` error therefore reaches the `aw group` shape too. Measured: for
a roadmap under `.aw/records/roadmaps/` whose declared `set:` disagrees with its filename,
`check_name_identity` emits `recovery='aw group research bbb222 --set <setid> --rename --apply'`, and
running `aw group research bbb222 --set newset --rename` exits 2 with `no research artifact matched
'bbb222'`, while `aw group roadmaps bbb222 --set newset --rename` exits 0 and previews.

The consequence is asymmetric in an important way: E-02's fix ALREADY corrects this, for free, because
all three shapes share the lookup. The gap is in the EVIDENCE. E-01 and E-03 as written exercise only
`aw rename`, so the plan could have been executed, validated, and reported done with the `aw group`
hint still printing a refusing command, which is precisely the defect class this plan exists to close.
That is why it is HIGH rather than a note. Fixed by adding F-14, extending E-01 to a third case on the
`Set`/`aw group` branch, requiring E-03 to cover the `aw group` shape for at least one non-roadmap type,
requiring E-02's diff to show the lookup replaced at ONE site (a second derivation is now a finding
against V-02), adding the obligation to E-04's comment, and extending V-01/V-02/V-03 and the evidence
contract.

**E-01's RESEARCH-TREE MIRROR CANNOT BE BUILT AS DESCRIBED (PR-702, MEDIUM).** E-01 asks for a
`roadmaps/` fixture whose declared `- Id:` is absent from its filename plus "the mirror case, a
`.roadmap.md` filed in the RESEARCH tree". The `roadmaps/` half works (measured: the finding fires with
`recovery='aw rename research zz9zz9 --to-id6 --apply'`, static noun exits 2, derived noun exits 0). The
mirror is caught between two constraints. Give it a PRE-ID6 name and `research_contract.parse_name`
rejects it (it requires the `YYYYMMDD-<set>-<NN>-<id6>-<slug>` core), so `research_archive`'s
confinement refuses the very command the control must show RESOLVING, with `selector 'yy8yy8' matched no
research files within the research root`. Give it a CONFORMING name and `_identity_name_is_modern`
returns True, so `check_name_identity` skips the `Id` field and NO finding fires at all (measured:
`findings: 0`), which by this plan's own warning is a vacuous fixture. The resolution is to drive the
mirror through the `Set` field on a conforming name, which fires the finding AND lands on the `aw group`
branch PR-701 requires covering, so one fixture change satisfies both findings. Fixed in E-01 with the
measurement, F-15, V-01 (which now fails a mirror built either wrong way), and the evidence contract.

**E-03's SWEEP WAS ALREADY RUN AND ITS OPEN QUESTION ALREADY ANSWERED (PR-703, LOW).** E-03 asks the
executor to report any type whose derived noun differs from its static entry, and E-03/V-03 left open
whether the `plans` case needs an `87m438` dependency. Review ran both. Containment over a real record
of each of the eight mapped types agrees with the static entry for seven and differs only for
`roadmaps`, which IS the defect, so the regression surface on this repository is empty. And `aw rename
plans 7qx7ys --to-id6` exits 0 at HEAD, so the `plans` case passes BEFORE the sibling lands and the
plan's `- Item-Dependencies: none` is correct. Recording both turns an open executor question into a
stated expectation, so a second difference reads as a genuine surprise rather than expected noise.
Also corrected: V-03 said "seven mapped types" where the map has eight entries (it omitted `roadmaps`
itself, the subject of the plan).

NOT RAISED, each checked and let stand. All three open questions are correctly resolved and each cites
a measurement rather than a preference; OQ-02 in particular is a HOW question whose resolution rests on
a reproduced measurement, meeting the demonstrate-do-not-describe bar. The `low` priority is right and
honestly argued from the zero population, and filing it `bug` rather than `chore` is defensible since
the output is a wrong answer. The spec-sync section's readings of `2lcqno` N3 and `z7nbn1` 1.1 are fair,
including its refusal to write a filing rule into the naming spec. F-10's insistence on preserving the
id6-over-filename preference is correct and remains pinned. The Deferred entries' carriers all resolve.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. All three open questions remain resolved and non-blocking.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | high | UNDER-SCOPE | E. Testing and verification | `agent_workflows/check_engine.py` `_identity_rename_hint` (the three returns off one `rename_type = _IDENT_RENAME_TYPE.get(record_type)`); `artifact_types.TYPE_BACKENDS['roadmaps']['group']` is `artifact_rename.run_group_roadmaps`; review probe | The helper emits `aw group <t> <sel> --set <setid> --rename --apply` on its modern-plus-`Set` branch, and that shape carries the identical wrong-noun defect. E-02's fix corrects it for free (shared lookup), but E-01/E-03 exercise only `aw rename`, so the plan could be validated and reported done with the `aw group` hint still refusing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-14 added; E-01 gains a third case on the `Set`/`aw group` branch; E-03 must cover `aw group` for a non-roadmap type; V-02 now fails a diff containing a second derivation instead of one replaced lookup; E-04's comment must name the `aw group` shape; V-01, V-03, `- Scope:`, proposed changes and the evidence contract updated. |
| PR-702 | medium | IN-SCOPE | E. Testing and verification | plan E-01 (as authored); `research_contract.parse_name`; `check_engine._identity_name_is_modern`; `research_archive._resolve_research_for_mutation`'s `matched no research files within the research root`; review probe | E-01's research-tree mirror cannot be built as described: a pre-id6 research name fails `parse_name` so the control's own command refuses for an unrelated confinement reason, and a conforming name is MODERN so the `Id` field is skipped and no finding fires (`findings: 0`). Either way the control is broken or vacuous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 now specifies the mirror as a CONFORMING research name driven through the `Set` field, which fires the finding and lands on the `aw group` branch PR-701 needs; F-15 records both measured failure modes; V-01 fails a mirror built either wrong way; the evidence contract states it. |
| PR-703 | low | IN-SCOPE | G. Plan executability | plan E-03 and V-03 (as authored); `check_engine._IDENT_RENAME_TYPE` (eight entries); review sweep | E-03 left the executor to discover whether any type's derived noun differs and whether the `plans` case needs an `87m438` edge; both were answerable from the repository. Also V-03 said "seven mapped types" where the map has eight, omitting `roadmaps` itself. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-16 records the measured sweep (exactly one difference, `roadmaps`) and that `aw rename plans 7qx7ys --to-id6` exits 0 at HEAD so no dependency edge is owed; E-03 and V-03 now state the expectation and name all EIGHT types. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The `aw group` branch is equally broken. Widen this plan's tests to cover it, file a separate backlog item, or add a fifth child to the Set? | Widen this plan's tests; add no code and no new artifact. | (a) A separate backlog item: rejected because the FIX is already inside E-02 (all three shapes read one lookup), so a separate item would carry no code change and would leave this plan's own validation able to pass with half the defect live. (b) A fifth child in the Set: rejected for the same reason, and because the parent `95jk4s` is already reviewed with a four-child table whose coverage gate passed; adding a child for zero deliverable would inflate the Set. | Measured: `recovery='aw group research bbb222 --set <setid> --rename --apply'` from `check_name_identity`; `aw group research bbb222 --set newset --rename` `rc=2`; `aw group roadmaps bbb222 --set newset --rename` `rc=0`. The single `rename_type` lookup feeding all three returns. | yes |
| D-2 | E-01's mirror is unbuildable as described. Drop the mirror, build it on `Set`, or relax its oracle to something weaker than executability? | Build it on the `Set` field with a conforming research name. | (a) Drop the mirror: rejected because the asymmetry between the two trees is the plan's whole argument that a static map cannot serve both, so the control is load-bearing. (b) Relax the oracle to string comparison: rejected outright, as the plan's own F-13 identifies string-only assertions as the reason this defect class survives. | Measured three fixtures: pre-id6 research name -> both nouns `rc=2` with `matched no research files within the research root`; conforming research name on `Id` -> `findings: 0`; conforming research name on `set:` -> finding fires with the `aw group` recovery. | yes |
| D-3 | Should review answer E-03's per-type question and the `plans`/`87m438` dependency question, or leave them for the executor as the plan does? | Answer both now and record the measurements as expectations. | (a) Leave them open: rejected because both are facts the repository answers in one command each, and leaving the dependency question open means a plan whose `- Item-Dependencies:` correctness is unresolved at approval time, which a reviewer should not pass on. | Derivation per type over a sampled real record: seven agree, `roadmaps` differs. `aw rename plans 7qx7ys --to-id6` -> EXIT 0 at HEAD. | yes |
