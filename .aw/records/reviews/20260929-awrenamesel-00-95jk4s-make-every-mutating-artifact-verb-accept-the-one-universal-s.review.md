# Review findings: plan 95jk4s

- Subject-Id: 95jk4s
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `7b91f150` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after, for the parent and for the one child edited. Because this plan's own first `- Kind:`
bullet reads `orchestrator`, the `IPD-S407` typed child-tracking row check applies; it reports no
violation, so no bounded repair loop was entered and no attempt log is owed. No pre-review snapshot
was owed: `git status --porcelain` was empty, so the plan was committed and unmodified. A bare
`python3 -m pytest` reports `3246 passed, 2 skipped, 3 warnings in 49.40s` plus the 207-test deselect
notice, reproducing F-10 exactly. No production file was modified: the one cross-type rename
measurement ran `cli.main` against a throwaway git repo under `tempfile.TemporaryDirectory`.

THE ORCHESTRATOR COVERAGE PREMISE HOLDS BY INSPECTION, which is the first thing to establish for an
Order-0 plan. All four children exist in `pending/` with `- Kind: child`, carrying 5, 6, 5 and 4
`E-*` items respectively, and the parent's four checklist rows are pure child confirmations whose
reasoning sits on continuation lines. Each of the four deliverables named in the child table is owned
by exactly one child, and no deliverable is parked on the parent, so the runner's retirement (which
skips the pre-transition E/V checkpoint) would not mark unperformed work complete. The children's front
matter is consistent with the parent's table in every field checked: `87m438` and `1x4tdo` both declare
`- Item-Dependencies: executed:eby93o`, `eby93o` and `3qxuw1` declare `none`, all four carry
`- From-Backlog: gyv9tf` and `- Blocks-Release: next` (correct, since backlog `gyv9tf` is `Work-Kind:
bug` and `graduated`), and the four `- Scope-Paths:` sets are genuinely disjoint across four production
modules and four not-yet-existing test files.

EVERY ONE OF THE PLAN'S TEN FINDINGS WAS INDEPENDENTLY REPRODUCED AND EVERY ONE HOLDS. F-01: `aw
rename plans <a filename> --to-id6` and `aw group plans <the same filename> --set zz` both EXIT 2 with
`no plan has Id '<filename>'`. F-02: the five resolver kinds are exactly as stated (`substring`,
`substring`, `path`, `id6`, `setid`). F-03, the load-bearing sequencing claim:
`selectors.resolve_for_mutation(repo,'plans',<a spec path>)` returns `(<the SPEC>, None)` with
`err=None`, and `plans_refs._find_plan_by_id` does iterate `plans_dir.rglob("*.md")` only, so the
ordering really is forced. F-04: a real `cli.main(["--no-interactive","rename","specs",<a plan
path>,"--slug","zzz","--apply","--dir",d])` exits 0, prints the rename line, and the original plan path
no longer exists. F-05: `aw archive plans <a filename>` prints `✓ CLEAN no terminal-root plan or Set
matches '<filename>'` at EXIT 0, and so does `aw archive plans nonexistent-token-xyz`, so a typo is
indeed indistinguishable from a clean tree. F-06: the terse setid finds nothing while the parenthesized
form matches. F-07: `TYPE_BACKENDS['roadmaps']['rename']` is `artifact_rename.run_rename_roadmaps`, `aw
rename roadmaps 7ny1bg --slug x` EXITs 0, and the hint's own command `aw rename research 7ny1bg
--to-id6 --apply` EXITs 2 with `no research artifact matched '7ny1bg'`. F-08: the four `Scope-Paths`
sets are disjoint. F-09: spec `z7nbn1` line 80 carries the quoted sentence verbatim and its Section 2.1
does say "largely SATISFIED FOR READERS". The `2lcqno` N3 citations resolve too, including "EXCEPT a
direct PATH" and "must be PINNED, never retired as dead code". Order 01's decisive design measurement
also reproduces: `selectors.resolve(repo,'research','effzzi')` returns a `.roadmap.md` file with
`kind='id6'` while `status_set.detect_artifact_type(<that file>, repo)` returns `roadmaps`, so the
type-equality predicate really would refuse a legitimate target.

THIS IS AN UNUSUALLY DISCIPLINED SET. The parent contributes no code, no test and no record; it
correctly refuses to restate its children's evidence; it corrects the backlog item in three places
(naming `group`, discovering `archive plans`, and refuting the roadmaps diagnosis) and records each
correction in the child that owns it; its five `Carrier-Declined` deferrals are each backed by a reason
about blast radius rather than effort; and its OQ-02 reasoning about `graduated` versus `done` and gate
inheritance is exactly right. Review found nothing wrong with the Set's decomposition, its ordering, or
its central design decision. What it found is that the parent UNDERSTATES the defect's reach in one
direction and OVERSTATES the Set's guarantee in another, plus one uncited precedent the guard must
reconcile with.

**THE CROSS-TYPE RENAME IS REACHABLE THROUGH SIX TYPE VERBS, NOT ONE (PR-501, MEDIUM).** F-04
demonstrates the defect through `specs` alone, and both the parent and Order 01 present it that way.
Measured across all eight renameable types, each against the SAME plan path in a fresh throwaway repo,
`specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps` AND `releases` each exit 0 and rename the
plan. This does NOT add a deliverable and does not change the fix: all six reach
`selectors.resolve_for_mutation` through the single call site in
`artifact_rename.run_rename_generic`, which takes `artifact_type` as a parameter, so Order 01's one
guard closes all six at once. What it changes is the stakes and the evidence owed: an E-05 sweep that
shows `specs` refusing does not establish that the shared site covers the other five. Fixed by widening
F-04, adding F-11 to the parent, and adding F-13 plus obligations on `eby93o`'s E-05 and V-05 (a
six-type refusal matrix, and an explicit account of the two types that do NOT reach the guard so
neither is miscredited to it).

**A CONFINEMENT PRECEDENT ALREADY EXISTS AND CHOSE THE OPPOSITE SHAPE, UNCITED BY EITHER PLAN
(PR-502, MEDIUM).** Order 01's E-03 mandates "REFUSE, NEVER SILENTLY DROP".
`research_archive._resolve_research_for_mutation` solves the same problem by DENYING `MATCH_PATH` up
front and then DROPPING out-of-root paths, refusing only `if paths and not confined`. Its docstring
attributes the design to IPD `me227c` E-04, so it is deliberate and shipped. Neither the parent nor
Order 01 mentions it (`grep` for `research_archive` and `me227c` returns zero hits in both). This
matters twice over: an executor who finds the sibling will reasonably think one of the two is wrong and
may "harmonize" them, and the sibling's deny-`MATCH_PATH` approach, if adopted on the rename surface,
would refuse the legitimate SAME-TYPE path selectors Order 01's own E-04 pins, inverting this Set's
purpose. Both behaviors are in fact correct, because the sibling filters a possible setid MULTI-match
(where dropping non-members is right) while the new guard rejects a single explicitly NAMED foreign
path (where silence would hide the operator's mistake). Fixed by adding F-12 to the parent, F-14 to
`eby93o`, and requiring E-03 to state the distinction in a comment that names the sibling, with V-03
refusing a comment that merely repeats "refuse, do not drop".

**COMPLETION CRITERION 2 CLAIMED MORE THAN THE SET DELIVERS (PR-503, MEDIUM).** It read "No mutating
verb acts on an artifact outside the type the operator named", an unrestricted universal. Order 01
guards `resolve_for_mutation`, which has exactly TWO production callers plus a shim, so it covers the
verbs that route through it and no others: `aw group` for the non-plans types, and any backend with its
own private matcher, are untouched, and the plans backends become covered only because Orders 02 and 03
route them there. `research` is out of the guard's reach for a different, pre-existing reason (the
deny). Left unscoped, this is a criterion a later reader would judge the Set against and find it
failing on work it never claimed. Fixed by rewriting criterion 2 to name the six covered verbs and the
mechanism, and adding F-13 to the parent recording the call-site census.

**THREE LIVE-ARTIFACT COUNTS HAVE DRIFTED (PR-504, LOW).** F-06's corpus reads "908 plans declare a
Set" and "423 addressable"; re-measured, 965 and 472. Its `researchorg` match reads 3 plans; measured 8.
F-02's `findtier` setid reads 3 plans; measured 4. NO CONCLUSION MOVES, and the two figures the Set's
argument actually rests on (136 parenthesized, 77 unaddressable setids) are UNCHANGED. The plan already
tells each child to re-derive its baseline, and F-10 explicitly labels the suite total as drifting, so
this is a precision fix rather than a structural one: a reader could otherwise mistake the totals for
current. Fixed in F-02, F-06 and F-10, each now labelling the drifting figure as context and naming the
stable ones.

NOT RAISED, each checked and let stand. The parent's Scope-Paths naming only its own file is CORRECT
for a plan contributing no code, and it is what forced the two cross-plan fixes into `eby93o` rather
than into the parent. The parent's claim that Orders 02, 03 and 04 may run in parallel after 01 is
sound on the disjointness measurement, and the runner isolates worktrees anyway. The cross-IPD claim
that the sequencing is "pinned from the children's side" is accurate and was verified by reading both
children: `87m438` E-06(e) and `1x4tdo` E-05(e) each assert a foreign-type path is refused through
their newly routed backend, which can only pass with Order 01 in the tree. Order 04's independence is
real: it changes a suggested string in `check_engine` and touches no resolver. Both open questions are
non-blocking, resolved, and correctly owned by the author.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. Both pre-existing open questions survive review unchanged.

NOTE ON THE EDITED CHILD. `eby93o` was edited under the cross-plan rule (fix a finding in the owning
plan, cross-reference from the dependent), NOT reviewed. Its `- Status:` remains `to-review` and it
carries no `- Readiness:`, since writing one would assert a review that did not happen; its own
`## Workflow history` records the edit under a non-review label. The other three children were read as
evidence and were not modified.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | medium | UNDER-SCOPE | D. Anti-regression and domain invariants | `agent_workflows/artifact_rename.py` `run_rename_generic` (`selectors.resolve_for_mutation(repo_root, artifact_type, selector, force=...)`); review probe over all eight renameable types | The cross-type rename F-04 demonstrates through `specs` is reachable through SIX type verbs (`specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps`, `releases`), all one shared call site. One guard still closes all six, so no deliverable is added, but an E-05 sweep proving only `specs` does not establish coverage of the other five. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-04 widened with the eight-type matrix; parent F-11 added; `eby93o` F-13 added and its E-05/V-05 now require the six-type refusal matrix plus an account of the two types that do not reach the guard. |
| PR-502 | medium | UNDER-SCOPE | C. Architecture and operability | `agent_workflows/research_archive.py` `_resolve_research_for_mutation` (`deny=frozenset({selectors.MATCH_PATH})`, then the `relative_to(rroot_resolved)` drop loop, refusing only `if paths and not confined`); its docstring citing IPD `me227c` E-04 | A shipped sibling already confines a resolved set to one type's tree and chose the OPPOSITE of Order 01's "refuse, never silently drop", and neither the parent nor Order 01 cites it (zero grep hits in both). An executor may harmonize them wrongly; adopting the sibling's deny-`MATCH_PATH` shape would refuse the legitimate same-type path selectors Order 01's E-04 pins. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Parent F-12 and a new cross-IPD bullet added; `eby93o` F-14 added; E-03 must now state the multi-match-versus-named-path distinction in a comment naming the sibling and is forbidden from adopting deny-`MATCH_PATH`; V-03 refuses a comment that only repeats "refuse, do not drop". |
| PR-503 | medium | IN-SCOPE | G. Plan executability | plan completion criterion 2 (as authored); `grep -n 'resolve_for_mutation' agent_workflows/*.py` -> definition plus two production callers (`artifact_rename.py`, `research_archive.py`) and two `cli.py` comments | Criterion 2 was an unrestricted universal over "every mutating verb", which the Set does not deliver: the guard covers only verbs routing through `resolve_for_mutation`, so `aw group` for non-plans types and every private-matcher backend are unaffected, and `research` is out of reach by a different pre-existing mechanism. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Criterion 2 rewritten to name the six covered verbs and the routing mechanism, and to record that `research` refuses by DENY rather than by containment; parent F-13 added with the call-site census. |
| PR-504 | low | IN-SCOPE | Evidence freshness | re-measured at review: 965 plans declare a Set (plan says 908), 472 addressable (says 423), `researchorg` matches 8 (says 3), `findtier` matches 4 plans (says 3) | Four live-artifact counts have drifted. No conclusion moves and the two load-bearing figures (136 parenthesized, 77 unaddressable setids) are unchanged, but a reader could mistake the totals for current. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-02, F-06 and F-10 updated with re-measured values, each labelling the drifting figure as context and naming the stable ones; F-06 now tells Order 03 to re-derive rather than assert. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | PR-501 and PR-502 are findings the CHILD `eby93o` owns, but only the parent was in review scope and the parent's `Scope-Paths` names only its own file. Fix them in the child, describe them in the parent only, or add a fifth child? | Fix in `eby93o` (the owning plan) and cross-reference from the parent, editing no other child. | (a) Record them in the parent only: rejected because the parent is an orchestrator that must hold no work of its own, so an obligation written there would be retired unperformed when the runner skips the pre-transition checkpoint. (b) Add a fifth child: rejected because neither finding adds a deliverable; both are evidence and reconciliation obligations on work Order 01 already owns, and a new child would inflate the Set for nothing. | plan-review Step 2.4 ("fix it in the owning plan and cross-reference it from dependent plans"); AGENTS.md's orchestrator rule that work parked on a parent is marked complete having never been performed. | yes |
| D-2 | Does PR-501's six-type reach mean Order 01's guard is the wrong shape, or merely under-evidenced? | Under-evidenced only; the guard's shape is right and unchanged. | (a) Split per-type guards: rejected on measurement, since all six types traverse ONE call site that already receives `artifact_type`, so per-type work would duplicate a parameterized path. (b) Move the guard into `resolve`: rejected as the Set's own standing exclusion, and it would change what seventeen reader modules see for no safety gain, since only a mutation can damage anything. | `artifact_rename.run_rename_generic`'s single `resolve_for_mutation` call taking `artifact_type`; spec `z7nbn1` 2.1's seventeen-importer census; the parent's own cross-IPD exclusion. | yes |
| D-3 | Criterion 2 overclaims. Narrow the criterion, or widen the Set to cover every mutating verb? | Narrow the criterion to what the guard provably covers. | (a) Widen the Set: rejected as materially larger than the backlog item and unmeasured, since it would require auditing every private matcher across nine types and inventing policy for verbs with no shared resolver route. (b) Leave it as an aspiration: rejected because a completion criterion is the bar the Set is judged against, and an unmeetable one makes an honest executor unable to report done. | `grep` census showing two production callers of `resolve_for_mutation`; the measured `research` deny path; the plan's own "Under-scope" paragraph already conceding the reader side stays permissive. | yes |
