# IPD: Confine a path selector to the requested type tree so a mutating verb cannot rename a foreign artifact

- Date: 2026-09-29
- Kind: child
- Concern: `aw rename <type> <path>` RENAMES A FILE OF A DIFFERENT TYPE when handed a path outside the requested type's tree, because `selectors.resolve`'s FIRST precedence rule (`path`) matches an existing file regardless of the type it was asked about, and `artifact_rename.run_rename_generic` has no post-resolution type check. MEASURED AT AUTHORING against this lane's source, driving the real CLI in-process in a throwaway git repo: `aw rename specs <a PLAN path> --slug zzz --apply` exited 0 and printed `renamed .aw/records/plans/pending/20260929-demo-01-ab12cd-a-demo-plan.ipd.md -> .aw/records/plans/pending/20260929-demo-01-ab12cd-zzz.ipd.md`. A verb scoped to `specs` renamed a PLAN, and the original filename no longer existed on disk.
  THE REPOSITORY ALREADY KNOWS THIS IS A REAL HAZARD AND ALREADY GUARDS THE OTHER SURFACE, which is what makes this a defect rather than an unexplored design space. `status_set.run_set_command` carries an explicit `Type mismatch` refusal whose own comment says it is "the ONLY guard between it and a cross-type write", records the identical mechanism ("the pre-filter only narrows which types the RESOLVER is QUERIED for, while `selectors.resolve`'s FIRST precedence rule (direct PATH) matches an existing FILE regardless of the type it was asked about"), and states that deleting it was measured to let `aw specs set approved <a plan path> --by-human` rewrite a PLAN and append a forged human-approval attestation. Approved spec `2lcqno` N3 documents the SAME hole in as many words: "scoped resolution is type-safe for every selector kind EXCEPT a direct PATH". The status surface got the guard; the RENAME surface never did.
  THE RENAME SURFACE IS THE MORE DESTRUCTIVE OF THE TWO, which is why this is worth fixing rather than documenting. A wrong status write is a reversible text edit to a file that keeps its name. A wrong rename MOVES the file and then REWRITES EVERY IN-REPO CITATION of its old name (`artifact_rename` calls the reference rewriter after the move), so the damage is a tracked rename plus a scattered set of citation edits, and the artifact is no longer locatable by the name every other record cites.
  THIS MUST LAND BEFORE ORDER 02, and the ordering is measured rather than stylistic. The plans backend is the one backend that does NOT use the shared resolver, and its id-directed scan (`plans_refs._find_plan_by_id`, which iterates `plans_dir.rglob`) is STRUCTURALLY INCAPABLE of leaving the plans tree. Order 02 routes it through `selectors.resolve_for_mutation`, and measured at authoring, `resolve_for_mutation(repo,'plans',<a spec path>)` returns that SPEC with no error. So routing the plans backend first, without this guard, would IMPORT the escape into a backend that is currently immune to it.
- Scope: Add ONE containment predicate to `agent_workflows/selectors.py` and enforce it in `selectors.resolve_for_mutation`, so a resolved path that is not inside any of the requested type's own `record_dirs` is REFUSED with a message naming the requested type and the path, instead of being mutated. Enforce it at the MUTATION wrapper only, leaving the read-side `resolve` unchanged. Add the outcome tests this hole has none of. EXCLUDES: changing `selectors.resolve` precedence or its read-side behavior (every reader depends on the path rule and `aw find` is deliberately permissive); the `status_set` `Type mismatch` refusal (already correct, must stay byte-unchanged and must not be refactored into this predicate); routing the plans backend through the shared resolver (Order 02's fence); the `roadmaps` addressability question (Order 03's fence); and `archive`, which does not use `resolve_for_mutation` at all.
- Scope-Paths: agent_workflows/selectors.py, tests/test_selector_type_containment.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: gyv9tf
- Blocks-Release: next
- Set: awrenamesel
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: eby93o

## Workflow history

- 2026-09-29 cross-plan finding applied (opencode/its_direct-pt3-claude-opus-5-1m-us): THIS PLAN WAS NOT ITSELF REVIEWED; it is edited here because `/plan-review` of its Order-0 parent `95jk4s` produced two findings this plan OWNS, and the cross-plan rule requires fixing a finding in the owning plan rather than describing it in the parent. Its `- Status:` is deliberately unchanged at `to-review` and no `- Readiness:` is written, since no review of this plan has happened. ADDED: F-13, recording that the cross-type rename is reachable through SIX type verbs (`specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps`, `releases`), not just the `specs` case F-01 demonstrates, all through the single `artifact_rename.run_rename_generic` call site, so one guard still suffices and no deliverable is added; and F-14, recording that `research_archive._resolve_research_for_mutation` already confines to one tree by DROPPING rather than refusing, the opposite of E-03's prescription, for the legitimate reason that it filters a possible setid multi-match. E-05 and V-05 now require the six-type refusal matrix and an account of the two types that do not reach the guard; E-03 and V-03 now require a comment reconciling with the sibling and forbid adopting its deny-`MATCH_PATH` shape, which would refuse the same-type path selectors E-04 pins. No other content changed.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `gyv9tf`. THIS PLAN'S DEFECT IS NOT IN THE BACKLOG ITEM: the item reports a REFUSAL (`aw rename plans <filename>` fails), and this plan fixes a SILENT WRONG MUTATION found while measuring the item's proposed remedy. The chain was: the item asks that the plans backend accept what the generic one accepts, so authoring measured what the generic one accepts, and found it accepts a path belonging to ANOTHER TYPE and renames it (F-01). That makes this a PREREQUISITE rather than a bonus: Order 02 implements the item's request by routing plans through the same resolver, and measured at authoring that resolver hands back a SPEC when asked for a plan (F-05), so landing Order 02 first would widen the hole into a backend that is currently immune. The guard is therefore sequenced first and Order 02 declares the dependency. THE SHAPE WAS CHOSEN BY MEASUREMENT, NOT BY ANALOGY (F-06, F-07): the obvious shape, copying `status_set`'s `detect_artifact_type` comparison, was prototyped and REFUSES a legitimate target today, because the one research doc `aw rename research effzzi` resolves is TYPED `roadmaps` by that function (its facet-first branch matches any `.roadmap.md`). Containment in the type's own `record_dirs` was then measured across all 1823 (type,file) pairs in this repository with ZERO false refusals, and it closes the escape.

## Goal

Make a type-scoped mutating verb refuse a path belonging to another type, instead of silently renaming that foreign artifact and rewriting every citation of its old name.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the wrong mutation before changing anything

- [ ] E-01 REPRODUCE THE CROSS-TYPE RENAME AS A FAILING TEST, so the fix is demonstrated rather than asserted. Create `tests/test_selector_type_containment.py` and add a case that seeds a PLAN under `.aw/records/plans/pending/` in a temp git repo, runs `aw rename specs <that plan's path> --slug zzz --apply`, and asserts BOTH that the command REFUSES (nonzero) AND that the plan file is still at its original name. At HEAD this must FAIL on both halves: measured at authoring, rc was 0 and the plan had been renamed.
  ASSERT ON THE FILE SYSTEM, NOT ONLY ON THE EXIT CODE. The exit code alone is a weak pin: a future change could refuse for an unrelated reason while still having moved the file. The load-bearing assertion is that the foreign artifact is UNTOUCHED (same path, same bytes), which is the property a user depends on.
  DRIVE IT IN-PROCESS VIA `cli.main` UNDER `redirect_stdout`, NOT AS A SUBPROCESS. This is a measured hazard rather than a style preference: an editable install can make a subprocess `python3 -m agent_workflows` in a lane import the MAIN checkout, so a subprocess assertion can pass while the tree under test is unfixed (filed as `ccbe60`). `tests/test_group_verb_policy.py` already uses the in-process shape and is the model to copy.
  PASS `--no-interactive` AND DO NOT PASS `--yes`. Measured at authoring: `aw rename` has no `--yes` flag and argparse exits 2 with `unrecognized arguments: --yes`, which looks like a refusal and would make a broken test appear to pass. The global `--no-interactive` flag must precede the subcommand.
  SEED THE REPO WITH `git init`, because the applier moves files with `git mv` (`artifact_core.git_mv`).
  - Depends on: none
  - Expected outcome: A test FAILING at HEAD, showing `aw rename specs <a plan path> --apply` exited 0 and moved the plan.
  - Execution state: pending

- [ ] E-02 PIN THE CITATION DAMAGE, because it is what makes this worse than a reversible edit and no test covers it. Add a case that seeds the same foreign plan PLUS a second record whose body CITES that plan's filename, runs the same cross-type rename with `--apply`, and asserts the citing record's bytes are UNCHANGED. At HEAD the rename proceeds and the reference rewriter runs over the repository, so the citation is rewritten to name a file the citing record never meant.
  ASSERT ON THE CITING FILE'S BYTES, which is the observable outcome, rather than on whether the rewriter was called.
  - Depends on: none
  - Expected outcome: A second test FAILING at HEAD, showing an unrelated record's citation was rewritten by a rename the verb should never have performed.
  - Execution state: pending

### Task group 2: the containment guard

- [ ] E-03 ADD ONE CONTAINMENT PREDICATE AND ENFORCE IT IN `selectors.resolve_for_mutation`. Add a helper to `selectors.py` that answers whether a resolved path lies inside any directory `selectors.record_dirs(repo_root, record_type)` returns, then call it in `resolve_for_mutation` for every resolved path and return a refusal naming the requested TYPE and the offending PATH when one is not contained.
  ENFORCE AT THE MUTATION WRAPPER, NOT IN `resolve`, AND THIS FENCE IS LOAD-BEARING. `resolve` is the READ-side authority used by `aw find`, `attention`, the runners, the checkers and the status setters (spec `z7nbn1` 2.1 counts seventeen importing modules), and its path rule is deliberately permissive so a reader can ask about any file. Narrowing `resolve` would change what every reader sees. `resolve_for_mutation` is documented as the wrapper that "applies the kind-aware ambiguity policy" for MUTATING verbs and is exactly where a mutation-only restriction belongs. Its existing refusals are the precedent: it already returns `(paths, error_message)` and already refuses a unique-kind collision outright as "a data bug to fix, not overridable by --force".
  USE CONTAINMENT IN `record_dirs`, NOT `status_set.detect_artifact_type`, AND DO NOT "SIMPLIFY" IT TO THE LATTER. This is the plan's one real design decision and it was settled by measurement (F-06, F-07). Copying the `status_set` comparison would REFUSE A LEGITIMATE TARGET TODAY: `aw rename research effzzi` resolves a real research document, and `detect_artifact_type` types that file `roadmaps`, because its facet-first branch returns the first type whose `TYPE_FACET` suffix the name ends with and the file is named `....roadmap.md`. Measured: `detect_artifact_type(<that file>) == 'roadmaps'` while `resolve(repo,'research','effzzi')` returns it with `kind='id6'`. A type-equality guard would therefore break the only spelling that works for that record. Containment asks the narrower and correct question ("is this file in the tree I was asked about"), and was measured across ALL 1823 (type,file) pairs in this repository with ZERO false refusals.
  REFUSE, NEVER SILENTLY DROP. A dropped path would leave `paths` empty and surface as the generic `no <type> artifact matched`, which misdescribes the situation and is the "silent no-match" the module's own docstring forbids for a denied kind. The message must name the requested type and the path, so an operator can see they asked the wrong verb.
  AND RECONCILE WITH THE SHIPPED SIBLING THAT DOES THE OPPOSITE, IN A COMMENT, because a reader who finds it will otherwise think one of the two is wrong (F-14, review). `research_archive._resolve_research_for_mutation` confines to one tree by DENYING `MATCH_PATH` and then DROPPING out-of-root paths, refusing only when every path was dropped. Both behaviors are correct because they answer different questions: that helper is filtering a possibly-MULTI-member result (it accepts a setid multi-match, where dropping non-members is right), while this guard fires on a single explicitly NAMED path, where the operator asked for one specific file with the wrong verb and silence would hide it. State that distinction where the predicate lives. DO NOT adopt the deny-`MATCH_PATH` approach here instead: it would refuse the legitimate SAME-TYPE path selectors E-04 pins, which is the opposite of this Set's purpose.
  DO NOT LET `--force` OVERRIDE IT. `--force` exists for a substring multi-match, an ambiguity the operator can legitimately resolve. A cross-type path is not ambiguous: it is the wrong verb for the file, and the module already establishes that not every refusal is forcible.
  KEEP THE PREDICATE PURELY PATH-BASED AND READ NO FILE CONTENT, so it cannot change any matching answer and costs nothing: `record_dirs` is already cached (`_record_dirs_cached`) and is already called on every `resolve`.
  - Depends on: E-01, E-02
  - Expected outcome: `aw rename <type> <a foreign-type path>` refuses naming the type and the path, leaves the file and every citation of it untouched, and E-01/E-02 pass.
  - Execution state: pending

### Task group 3: prove nothing legitimate broke

- [ ] E-04 PIN THE LEGITIMATE CASES THE GUARD MUST NOT REFUSE, which is the whole risk of this change. Add cases asserting that, for each of `plans`, `specs`, `backlog` and `research`, a record of that type is still resolvable for mutation by (a) its own repo-relative PATH, (b) its own ABSOLUTE path, and (c) its `id6`, all still reaching the rename preview.
  ADD THE `effzzi`-SHAPED CASE EXPLICITLY, because it is the one measured near-miss and the reason the predicate is containment rather than type equality (F-07). Seed a research document whose filename carries the `.roadmap.md` facet, and assert `aw rename research <its id6>` still resolves it. This test FAILS if someone later "simplifies" the predicate to a `detect_artifact_type` comparison, which is precisely the regression worth pinning.
  ADD THE SETID CASE, so a legitimate multi-target mutation still works: a setid naming several records of the requested type must still resolve to all of them, since `resolve_for_mutation` documents a setid multi-match as "an intentional multi-target" needing no `--force`.
  - Depends on: E-03
  - Expected outcome: Every in-tree selector kind still resolves for every type tested; the research-roadmap case passes and would fail under a type-equality predicate.
  - Execution state: pending

- [ ] E-05 PROVE THE BLAST RADIUS ON THE REAL CORPUS AND ON THE OTHER SURFACES. Run a sweep over this repository's own records asserting the predicate accepts every (type, own-file) pair, so the guard is shown not to refuse anything real, and confirm the READ side is unchanged by checking that `aw find` still resolves a path selector exactly as before.
  COVER ALL SIX AFFECTED TYPE VERBS, NOT JUST `specs` (F-13, review). The defect is reachable through `specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps` AND `releases`, all one code path in `artifact_rename.run_rename_generic` taking `artifact_type` as a parameter, so ONE guard closes all six and this item proves it did: show a foreign-type path REFUSED for each of the six. Also record the two types that do NOT reach the guard and WHY, so a reader does not mistake their behavior for this guard's work: `research` refuses a path earlier by DENYING `MATCH_PATH` (F-14), and `plans` refuses only because its private id-directed matcher cannot resolve a path at all until Order 02 routes it.
  ASSERT THE `status_set` GUARD IS UNTOUCHED AND STILL FIRES. `status_set.run_set_command`'s `Type mismatch` refusal is pinned by `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing`, and its own comment warns against reading it as dead code. This plan adds a SECOND guard on a DIFFERENT surface; it must not be read as replacing the first. Show that test still passes and that `status_set.py` is byte-unchanged.
  - Depends on: E-03
  - Expected outcome: Zero false refusals across the real corpus, the read side provably unchanged, and the pre-existing status-surface guard still in force.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here is by symbol.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).
- Tests must assert OBSERVABLE BEHAVIOR, never code structure: no `inspect`/`ast`/regex reads of production source, no symbol censuses (AGENTS.md, GUIDING_PRINCIPLES P16). Every test this plan adds drives a real verb through `cli.main` and asserts on exit codes and on file-system state.
- `aw rename` is ONE generic parser registered in a verb loop over six verbs, not a per-noun subcommand family; the type is a required positional and the selector is `nargs="*"`. The per-type handler comes from `artifact_types.TYPE_BACKENDS`, resolved lazily by `artifact_types.resolve_backend`.
- `aw rename` has NO `--yes` flag; passing one exits 2 at argparse with `unrecognized arguments`. Use the global `--no-interactive` before the subcommand to take non-interactive defaults.
- `selectors.record_dirs` returns only EXISTING directories and returns `[]` for an unknown or unresolvable type, so a containment predicate must decide what an EMPTY dir list means rather than assuming at least one dir exists (see OQ-02).
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`; verify the staged set, since this checkout is shared (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | A TYPE-SCOPED RENAME MUTATES A FOREIGN ARTIFACT AT THIS HEAD. `aw rename specs <a PLAN path> --slug zzz --apply` exits 0, renames the plan, and the original filename is gone. | Throwaway git repo seeded with one plan; `cli.main(["--no-interactive","rename","specs",str(plan),"--slug","zzz","--apply","--dir",d])` -> rc 0, `renamed .aw/records/plans/pending/20260929-demo-01-ab12cd-a-demo-plan.ipd.md -> ...-zzz.ipd.md`; `plan.exists()` -> `False`; directory listing showed only the renamed file. |
| F-02 | Root cause: `selectors.resolve`'s FIRST precedence rule is `path`, which matches an existing file regardless of the requested type, and `artifact_rename.run_rename_generic` applies no post-resolution type check; it takes `paths[0]` from `resolve_for_mutation` and proceeds. | `resolve`'s own docstring lists precedence `1. path ... 2. id6 ...`; `resolve(repo,'specs',<a plan path>)` returns that plan with `kind='path'`; `run_rename_generic` reads `src = paths[0].resolve()` with no type comparison. |
| F-03 | THE REPOSITORY ALREADY IDENTIFIED THIS EXACT MECHANISM AND GUARDED THE OTHER SURFACE, so this is a known hazard left unguarded on rename rather than an unexplored case. `status_set.run_set_command` carries a `Type mismatch` refusal whose comment states it is "the ONLY guard between it and a cross-type write" and that deleting it let `aw specs set approved <a plan path> --by-human` rewrite a PLAN and forge a human-approval attestation. | The refusal and its `setidfix w2y5ac E-02` comment in `status_set.run_set_command`; pinned by `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing`. |
| F-04 | APPROVED SPEC `2lcqno` N3 DOCUMENTS THE HOLE IN AS MANY WORDS and names the path kind as the sole exception, so closing it implements an approved contract rather than inventing policy. | `2lcqno` N3: "scoped resolution is type-safe for every selector kind EXCEPT a direct PATH, because `selectors.resolve`'s path precedence matches an existing file regardless of the type requested." |
| F-05 | THIS MUST PRECEDE ORDER 02. The plans backend cannot escape its own tree today (`plans_refs._find_plan_by_id` iterates `plans_dir.rglob`), but the resolver Order 02 routes it to CAN: asked for a `plans` artifact and given a spec path, it returns the SPEC with no error. | `selectors.resolve_for_mutation(repo,'plans','.aw/records/specs/implemented/20260817-2147-01-uniform-artifact-naming-grammar.spec.md')` -> `err=None`, one path, the SPEC. |
| F-06 | THE OBVIOUS FIX IS WRONG AND WAS MEASURED TO BE WRONG. Reusing `status_set.detect_artifact_type` for a type-equality check would REFUSE A LEGITIMATE TARGET: the research document `aw rename research effzzi` resolves is typed `roadmaps` by that function, because its facet-first branch matches any name ending `.roadmap.md`. | `detect_artifact_type(<.../20260821-awoptimize-03-effzzi-...roadmap.md>)` -> `'roadmaps'`, while `resolve(repo,'research','effzzi')` -> that same file with `kind='id6'`. Corpus sweep: 2 of 125 research candidates are cross-typed this way, both `.roadmap.md`. |
| F-07 | CONTAINMENT IS EXACT ON THE REAL CORPUS: it accepts every legitimate target and refuses every foreign path tested. This is the measurement that chose the predicate. | Sweep over all 9 types, 1823 (type,file) pairs: wrongly refused = 0. Foreign-path cases: `('specs', <plan path>)` -> False, `('plans', <spec path>)` -> False, `('roadmaps', <research-tree .roadmap.md>)` -> False, `('research', <that same file>)` -> True. |
| F-08 | ONLY THE `path` KIND CAN ESCAPE, so a guard scoped to containment is sufficient and needs no per-kind special casing. Every other kind is already directory-scoped because `_iter_paths` enumerates only `record_dirs(repo_root, record_type)`. | `resolve(repo,'specs',<a plan path>)` -> `kind='path'`; the two in-tree cross-typed research matches resolve with `kind='id6'` and are inside the research tree, so containment accepts them. |
| F-09 | THE DAMAGE EXCEEDS THE RENAME: `artifact_rename` rewrites in-repo citations of the old name after moving the file, so a wrong rename also edits unrelated records. | `run_rename_generic` performs the reference rewrite after the move (its `to_id6 and update_refs and src.name != new_name` branch and the surrounding rewrite path); the live `aw rename roadmaps 7ny1bg --slug x` preview on this repository listed 4 citation rewrites in 2 unrelated backlog records. |
| F-10 | `aw rename` HAS NO `--yes` FLAG; passing one is an argparse error, which would make a naive test appear to pass for the wrong reason. | `cli.main([...,"rename","specs",...,"--apply","--yes",...])` -> rc 2, `agent-workflows: error: unrecognized arguments: --yes`, file untouched. Re-run with `--no-interactive` and no `--yes` -> rc 0 and the file WAS renamed. |
| F-11 | Baseline is clean in this lane, so any failure after the change is attributable to it. THE ABSOLUTE COUNT DRIFTS AND IS NOT A BAR: re-derive it on your own clean tree. | `python3 -m pytest` -> `3246 passed, 2 skipped, 3 warnings in 51.44s`. |
| F-12 | No existing test covers cross-type containment on the RENAME surface. The only type-mismatch test in the repository covers the STATUS surface (`aw set`), and the rename tests exercise same-type filename/path selectors only. | `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing` targets `status_set`; `tests/test_spec_id6_filenames.py` and `tests/test_artifact_refs_rewrite.py` pass paths and filenames of the SAME type they scope to. |
| F-13 | REVIEW FINDING (parent `95jk4s` PR-501), WIDENING F-01 RATHER THAN CHANGING THIS PLAN'S SCOPE: the cross-type rename is reachable through SIX type verbs, not just the `specs` one F-01 demonstrates. One guard at `resolve_for_mutation` closes all six, because all six are ONE code path taking `artifact_type` as a parameter, so no new deliverable arises. What it changes is E-05's sweep, which must now show the guard refuses a foreign path for EACH of the six rather than for `specs` alone, and must record that `research` is out of reach by a DIFFERENT pre-existing mechanism (F-14). | Re-measured at review in a fresh throwaway repo, each type against the SAME plan path: `specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps`, `releases` each EXIT 0 and RENAME THE PLAN; `research` EXITs 2 (`this verb does not accept a path selector`); `plans` EXITs 2 (`no plan has Id '<path>'`). Single shared call site: `artifact_rename.run_rename_generic`'s `selectors.resolve_for_mutation(repo_root, artifact_type, selector, force=...)`. |
| F-14 | REVIEW FINDING (parent `95jk4s` PR-502): A CONFINEMENT PRECEDENT ALREADY EXISTS AND THIS PLAN DOES NOT CITE IT, AND IT CHOSE THE OPPOSITE SHAPE TO E-03's "REFUSE, NEVER SILENTLY DROP". `research_archive._resolve_research_for_mutation` confines a resolved set to one type's tree by DENYING `MATCH_PATH` up front and then DROPPING out-of-root paths, refusing only when EVERY path was dropped. That is not a contradiction to resolve by changing E-03: the sibling accepts a SETID MULTI-MATCH, where dropping non-members is the correct behavior, whereas this guard fires on a single explicitly named foreign PATH, where refusing is correct. E-03 must state that distinction rather than appear to overrule a shipped sibling, and must NOT adopt the deny-`MATCH_PATH` approach wholesale, which would break the legitimate same-type path selectors E-04 pins. | `agent_workflows/research_archive.py` `_resolve_research_for_mutation` passes `deny=frozenset({selectors.MATCH_PATH})`, then `for p in paths:` skips any failing `p.resolve().relative_to(rroot_resolved)`, returning `selector '<s>' matched no research files within the research root` only `if paths and not confined`. Its docstring attributes the design to IPD `me227c` E-04. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_selector_type_containment.py` with a failing case proving `aw rename specs <a plan path> --apply` renames the plan (E-01).
2. Add a failing case proving the same wrong rename rewrites an unrelated record's citation (E-02).
3. Add a containment predicate to `selectors.py` and enforce it in `resolve_for_mutation`, refusing a resolved path outside the requested type's `record_dirs`, not overridable by `--force` (E-03).
4. Add the must-not-refuse guards: path, absolute path and id6 for four types, the `.roadmap.md`-named research document, and a setid multi-target (E-04).
5. Sweep the real corpus for false refusals, show the read side unchanged, and show the pre-existing `status_set` guard still in force and byte-unchanged (E-05).

## Deferred / out of scope (with reason)

- ROUTING THE PLANS BACKEND through the shared resolver, which is the backlog item's literal request. It is the next Order in this Set and depends on this guard.
  - Carrier: 87m438
- THE `roadmaps` ADDRESSABILITY DEFECT (a `.roadmap.md` filed in the research tree is not reachable as `roadmaps`, and the `check_engine` workaround emits a command that refuses for the one file actually under `roadmaps/`). Found while measuring F-06 and genuinely separate: it is a question about which tree owns a record type, not about whether a mutating verb may leave the tree it was given.
  - Carrier: 95jk4s
- `aw archive plans`, which has its own non-shared matcher and does NOT call `resolve_for_mutation`, so this guard does not reach it. Its defects are real and measured (a filename selector exits 0 with a silent no-op; a terse setid fails whenever the `- Set:` value carries a descriptive parenthetical) but they are a different resolver on a different verb.
  - Carrier: 95jk4s
- UNIFYING THIS GUARD WITH `status_set`'s `Type mismatch` REFUSAL into one shared predicate. Tempting and deliberately declined: the two answer DIFFERENT questions (that one compares a DETECTED type, this one tests TREE CONTAINMENT), and F-06 measures that the detected-type question gives the WRONG answer for a research document named `.roadmap.md`. Merging them would either break `aw rename research effzzi` or weaken the status guard whose own comment warns against touching it.
  - Carrier-Declined: the two predicates are not the same predicate; measured that substituting one for the other refuses a legitimate target, and the status guard is pinned by its own test with an explicit do-not-delete rationale.
- WIDENING `resolve` ITSELF so no reader can address a foreign-type path. Declined: the read side is deliberately permissive, seventeen modules import it, and `aw find <a path>` answering about any file is useful and harmless. A mutation-only restriction gets the safety without changing what readers see.
  - Carrier-Declined: unmeasured blast radius across seventeen importers for no safety gain, since the harm requires a MUTATION and the mutation wrapper is the one chokepoint.

## Scope check

- Over-scope: none. The two declared paths are the module holding the resolver and a new test file dedicated to this hole. `agent_workflows/artifact_rename.py` is deliberately NOT in scope: the guard belongs in the resolver wrapper every mutating backend already calls, so fixing it at one site covers all eight generic types at once rather than editing each backend. `agent_workflows/status_set.py` is NOT in scope and must stay byte-unchanged.
- Under-scope: this does not guard `aw archive plans`, which uses its own matcher and never calls `resolve_for_mutation`, and it does not make `resolve` itself type-safe for readers. Both are accepted deliberately and recorded above with carriers. A reviewer who wants `archive` in the same pass should say so, accepting that it means changing a second, unrelated resolver.

## Required tests / validation

- The new cases in `tests/test_selector_type_containment.py`: the cross-type rename, the citation damage, the must-not-refuse matrix over four types and three selector kinds, the `.roadmap.md`-named research document, and the setid multi-target.
- FAILING-FIRST CONTRAST IS MANDATORY, not optional: run E-01's and E-02's cases against UNFIXED source and paste the failures, then against the fixed tree and paste the passes. A fix whose tests were never seen to fail has not been demonstrated, and for this defect the failing run is also the proof that the wrong mutation was real.
- Bare `python3 -m pytest` before and after, with both summary lines pasted. MEASURE YOUR OWN BASELINE ON A CLEAN TREE and compare against that, not against F-11's `3246`, which drifts with every intervening commit. The bar is ZERO FAILURES and a passed-count delta of exactly the new cases.
- The pre-existing status-surface guard still passes: run `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing` and paste the result.
- Negative proof that the fence held: `git diff --stat` shows no change to `agent_workflows/status_set.py`, `agent_workflows/artifact_rename.py` or `agent_workflows/plans_refs.py`.
- `aw sanitize --agent` clean (no maintainer/machine identifiers in anything authored).

## Spec / documentation sync

No spec amendment is required and no `.spec.md` file is in `Scope-Paths`, and that conclusion rests on reading the two specs that govern this behavior rather than on a grep miss.
- Approved spec `2lcqno` N3 already states the hole as a KNOWN EXCEPTION ("type-safe for every selector kind EXCEPT a direct PATH") and already names the existing refusal as the only guard on it, requiring that refusal be "PINNED, never retired as dead code". This plan ADDS a second guard on a second surface, which is what N3 contemplates; it does not change the contract, and it deliberately leaves the refusal N3 names untouched.
- Spec `z7nbn1` 1.1 requires that "a selector that resolves for one verb MUST resolve identically for every other verb". This plan is consistent with it: the guard restricts only MUTATION, and 1.1's own measurement section (2.1) frames the universal selector as satisfied "FOR READERS", so narrowing a mutating wrapper does not contradict it. If a reviewer reads 1.1 as covering mutating verbs too, the honest statement is that a cross-type path must refuse everywhere, which is what this plan makes true for eight types.
IF THE EXECUTOR FINDS a spec or README sentence asserting that a mutating verb may act on a path outside its type's tree, that discovery changes this section: stop, add the file to `Scope-Paths`, amend it in the same change, and say why here, per the plan-may-amend-a-spec rule.

## Open questions

### OQ-01: Should the guard compare a DETECTED type or test TREE CONTAINMENT?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, TREE CONTAINMENT. The detected-type shape is the obvious one, matches the existing `status_set` guard, and was prototyped first; it is WRONG for this repository because `status_set.detect_artifact_type` types any `.roadmap.md` file as `roadmaps` via its facet-first branch, and one such file is a RESEARCH document that `aw rename research effzzi` resolves today by id6 (F-06). A type-equality guard would refuse that legitimate target. Containment asks the narrower question the defect actually poses (did the resolver hand back a file outside the tree I asked about) and was measured across all 1823 (type,file) pairs in this repository with zero false refusals, while refusing every foreign path tested (F-07). E-04 pins the distinction with a test that fails under the type-equality shape, so the decision cannot be silently reverted.

### OQ-02: What should containment do when `record_dirs` returns an EMPTY list for a type?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, FAIL OPEN (skip the check) AND NOT FAIL CLOSED, because `record_dirs` returns only EXISTING directories and returns `[]` for an unknown or unresolvable type. Failing closed would make every mutating verb refuse in a repository where the type's directory has not been created yet, converting a missing-directory condition into a blanket refusal. Failing open is also harmless in that state: with no directories, `_iter_paths` yields nothing, so the only selector kind that can resolve at all is a direct path, and a repository with no records tree for the type has nothing to protect. Note this is not merely theoretical for tests: `tests/test_group_verb_policy.py`'s fixture is a bare `git init` with no records tree, so a fail-closed predicate would change the output of existing tests. The executor must verify that claim rather than trusting it, since those tests assert on specific messages.

### OQ-03: Should `--force` be able to override a cross-type refusal?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NO, and the module's own policy is the precedent. `resolve_for_mutation` already documents a UNIQUE-kind multi-match as "a data bug to fix, not overridable by --force", establishing that not every refusal is forcible. `--force`'s documented purpose is a filename SUBSTRING multi-match, a genuine ambiguity the operator can resolve. A cross-type path is not ambiguous at all: exactly one file matched, and it is the wrong kind of thing for the verb. The correct operator response is to run the verb for the right type, which the refusal message names.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The pytest output for the cross-type case run against UNFIXED source, pasted verbatim, showing it FAILING, together with the observed rc (`0`) and the observed post-run directory listing proving the plan was renamed. A pass here is a FAILURE of this validation: a test that does not fail at HEAD does not pin this defect. Also state explicitly that the invocation used `--no-interactive` and did NOT pass `--yes`, since per F-10 a stray `--yes` produces an argparse error that mimics a refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The citation case FAILING against unfixed source, pasted, showing the before and after bytes of the citing record and the specific citation text that was rewritten. Plus a one-line statement that the assertion is on the citing FILE'S BYTES and not on whether the rewriter was invoked.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: E-01's and E-02's cases now PASSING, pasted; plus the actual refusal message text, which must name both the requested type and the offending path. Plus the `git diff` of `selectors.py` showing the predicate and its call inside `resolve_for_mutation` (not inside `resolve`). Plus a run showing `--force` does NOT override the refusal. Plus negative proof of the fence: `git diff --stat` listing none of `status_set.py`, `artifact_rename.py`, `plans_refs.py`. PLUS the reconciliation comment quoted (F-14), checked to name `research_archive._resolve_research_for_mutation`, to say why dropping is right there and refusing is right here, and to warn against adopting deny-`MATCH_PATH` on this surface; a comment that merely says "refuse, do not drop" without naming the sibling does NOT satisfy this item, because the next reader's question is why the two differ.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pytest output for the must-not-refuse matrix, pasted, naming each (type, selector-kind) pair covered. For the research-roadmap case, paste the resolution result for `aw rename research <id6>` on a `.roadmap.md`-named document AND paste the value `status_set.detect_artifact_type` returns for that same file, so the record shows WHY a type-equality predicate would have refused it. For the setid case, paste the multi-target resolution showing all members still resolve without `--force`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: The corpus sweep output showing the count of (type, own-file) pairs checked and `0` wrongly refused. Plus `aw find plans <a path selector>` still returning that path, proving the read side is unchanged. Plus the pasted result of `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing` passing and `git diff --stat` showing `status_set.py` unchanged. Plus the bare `python3 -m pytest` summary after the change compared against the baseline YOU measured before editing (not F-11's number), with the delta shown to be exactly the new cases and zero failures. PLUS the SIX-TYPE refusal matrix (F-13): a foreign-type path refused for each of `specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps` and `releases`, pasted per type, since a single `specs` case does not establish that the shared call site covers the others. PLUS a statement of what `research` and `plans` do and WHY, naming the deny-`MATCH_PATH` mechanism and the id-directed matcher respectively, so neither is miscredited to this guard.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was authored `to-review` with no `- Readiness:` field, correctly, since that value is an output of review rather than of authoring. It must not be executed on the strength of the authoring turn.

EXECUTION CONTRACT. Stay inside `Scope-Paths`: `agent_workflows/selectors.py` and `tests/test_selector_type_containment.py`. Put the guard in `resolve_for_mutation`, NOT in `resolve`. Leave `status_set.py`, `artifact_rename.py` and `plans_refs.py` byte-unchanged. Do NOT implement the guard as a `detect_artifact_type` type comparison: E-04 pins the measured reason (F-06) and that shape refuses a legitimate target. Commit through `aw commit <plan> -- <paths>` with the staged set verified (the checkout is shared); never `git add -A`, never push, never `--no-verify`.
EVIDENCE CONTRACT. The failing-first contrast in V-01 and V-02 is the gate: if the new tests cannot be observed failing against unfixed source, stop and report rather than proceeding, because the wrong mutation has then not been pinned. Paste actual runner output for every `V-*`; never record a pass not run. Be aware of the measured hazard behind E-01's in-process requirement: an editable install can make a subprocess `python3 -m agent_workflows` import the MAIN checkout rather than this lane (`ccbe60`), so a subprocess assertion can pass against unfixed source.
POST-GATE LIFECYCLE. On completion move this plan to `.aw/records/plans/executed/` only once `aw ipd lint --phase pre-transition` conforms and every `V-*` carries inspected evidence. The runner owns the transition in a managed lane (`aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001` there). Backlog item `gyv9tf` is set `graduated`, not `done`, by the authoring flow; do not close it here.
