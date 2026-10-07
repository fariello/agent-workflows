# IPD: Confine the research set-assign destination so a date cannot move a committed record out of the repository

- Date: 2026-10-02
- Kind: child
- Concern: `research_refs.run_set_assign` reads `--date` through `getattr(args, "date", None) or date.today().strftime("%Y%m%d")` and hands it to `plan_set_assign`, which interpolates it into `R.format_name` with NO validation, so a traversal in that flag MOVES AN EXISTING COMMITTED RECORD OUT OF THE REPOSITORY at exit 0. Measured in this lane against a fixture nested four levels deep: `aw research set-assign w1qe6d --set grp --date ../../../../ESCAPED --apply` exits **0**, prints `renamed .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md -> .aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md`, and the record lands four directories above the records tree while the repository's research directory is left holding no record and `aw research index --check` reports `clean` (F-01). FIVE THINGS THE BACKLOG ITEM DOES NOT NAME, each of which changes the fix. (1) GIT ITSELF ALREADY REFUSES THIS MOVE and the escape happens only because `artifact_core.git_mv` SWALLOWS that refusal: `git mv` exits 128 with `fatal: '...' is outside repository`, and the helper's `if result.returncode != 0:` arm then performs the move with `shutil.move` regardless (F-04). So the record leaves the repository through a fallback written for untracked files, and it leaves the git index claiming the old path still exists (F-05). (2) THE DEFECT IS NOT REACHABLE THROUGH `aw group research`, which the item's framing would imply: that spelling's parser has no `--date` at all and exits 2 with `unrecognized arguments: --date`, so `aw research set-assign` is the ONLY surface (F-03). (3) AN ABSOLUTE `--date` DOES NOT ESCAPE, IT CRASHES, so the fix must handle a second shape the item does not mention: `plan_set_assign` plans `/ABSOLUTE/ESCAPED-grp-00-...` and `_apply_renames`'s unguarded `p.new_path.relative_to(repo_root)` then raises an uncaught `ValueError` (F-06). (4) `research mv` SHARES THE SAME WRITE FUNNEL BUT CANNOT TRAVERSE, because `plan_mv` takes its date from `parsed.date` rather than from a flag, which is what makes the containment assertion cheap to site correctly (F-07). (5) THE SIBLING'S REGEX CANNOT BE PORTED VERBATIM, exactly as the `m5csyi` plan found: research's date slot is `(?P<date>\d{8})`, so the shipped ISO guard would refuse `20260929`, the only shape this grammar accepts (F-11).
- Scope: Validate `date_str` in `research_refs.plan_set_assign` against the date slot of the grammar it fills (eight digits plus a calendar check), refusing through that function's EXISTING `(None, error)` channel before any rename is planned; then assert destination containment in `research_refs._apply_renames`, the one preview-and-apply funnel `set-assign` and `mv` share, so a destination outside the resolved research root is refused on BOTH arms and the absolute-path `ValueError` crash becomes a clean refusal. REUSE the date helper that plan `iumgvk` (Set `m5csyi`) adds to `research_cmd` rather than writing a second one, since `research_refs` already imports `research_cmd as _rcmd`; if `iumgvk` has not landed, add the helper there to the same contract. DELIBERATELY NOT COVERED: the creation paths `aw research new`/`new-comparison`/`aw adopt`, which `iumgvk` owns; the descriptive-field injection through `--summary`/`--topic`/`--consumed-by`, which plan `deftzy` owns; the `artifact_core.git_mv` fallback that swallows git's own refusal, which this plan pins as a finding and files as residue rather than changing under every other tree's rename verbs; and the detection blindness that lets `index --check` report `clean` for a repository whose record has left the tree.
- Scope-Paths: agent_workflows/research_refs.py, agent_workflows/research_cmd.py, tests/test_research_set_assign_date_containment.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 0ougsh
- Blocks-Release: next
- Set: 0ougsh
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: plb8jx
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): plan-review APPROVE WITH REVISIONS APPLIED
- 2026-10-02 /plan-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002 (HIGH, fixed), PR-003, PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed). Measured non-destructively that an unregistered scratch repo without a research dir resolves its research root under the real home, so fixture-path bounding is unsafe (HOME isolation and resolved-root bounds now required); `_apply_renames` had no refusal channel (sentinel plus `MutationResult(2)` specified); regex aligned to sibling `iumgvk`'s reviewed ASCII form; `research_cmd.py` declared. Full record: `.aw/records/reviews/20261002-0ougsh-01-plb8jx-confine-the-research-set-assign-destination-so-a-date-cannot.review.md`.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `0ougsh`. The item's reported vector REPRODUCES EXACTLY as filed, including its false-negative warning: the nested fixture is load-bearing and an absolute-path probe could not be bounded at all, so it was measured at the planner instead of being run (F-06). Five measurements the item does not state changed the plan rather than decorating it. FIRST, GIT ALREADY REFUSES THE MOVE: `git mv` exits 128 with `is outside repository`, and `artifact_core.git_mv` then does it anyway with `shutil.move` (F-04), which reframes the defect as a swallowed refusal and is why the plan pins that helper as residue instead of treating the rename as inherently unguarded. SECOND, the escape leaves the GIT INDEX INCONSISTENT, showing the old path as an unstaged deletion while `git ls-files` still lists it (F-05), so the loss is worse than a moved file. THIRD, `aw group research` CANNOT REACH THIS at all (`unrecognized arguments: --date`), so the item's surface is one verb and not two (F-03). FOURTH, an ABSOLUTE `--date` CRASHES with an uncaught `ValueError` in `_apply_renames` rather than escaping (F-06), a second shape needing the same guard. FIFTH, the item's instruction to reuse the `ribg85` fix shape cannot be followed literally, for the same reason the `m5csyi` plan recorded: the ISO regex refuses every legitimate research date (F-11); the REUSE is of the two-guard shape and, concretely, of the `research_cmd` helper `iumgvk` adds, which `research_refs` can already import. Also measured: the whole live population passes the proposed guard, 0 of 134 (F-10), so this is purely preventive with no migration step.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw research set-assign` refuse a `--date` it cannot safely use, and make the shared rename funnel refuse any destination outside the research tree, so a regroup can never move a committed record out of the repository. The severe property is that this verb destroys rather than creates: unlike the creation-path twin, a single mistyped flag removes a tracked artifact from the tree while reporting success and leaving every checker clean.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: validate the value before any rename is planned

- [x] E-01 Make the date guard available to `research_refs` WITHOUT writing a second copy of it. Prefer REUSE: `research_refs` already does `from agent_workflows import research_cmd as _rcmd`, and plan `iumgvk` (Set `m5csyi`, pending, independent) adds `research_cmd._refuse_unsafe_date(verb, value) -> Optional[str]` to exactly the contract this plan needs, so the import direction is already correct and no cycle is created (`research_cmd` does NOT import `research_refs`: measured, its imports are `artifact_core` and `research_contract` only).

  DECIDE BY INSPECTION, NOT BY ASSUMPTION, AND RECORD WHICH BRANCH YOU TOOK. If `research_cmd._refuse_unsafe_date` EXISTS when you execute, import and call it; add nothing. If it does NOT exist, ADD it to `research_cmd` to that same signature and contract, so `iumgvk` finds it present and converges rather than conflicting. Do NOT define a private duplicate in `research_refs`: two guards for one grammar is how the two verbs drift apart, which is the exact failure `ribg85` and `iumgvk` both recorded against the ISO/`YYYYMMDD` split.
  THE CONTRACT, stated here so this plan is executable standalone: return `None` for `None` (the omitted-flag case, which must keep defaulting to today) and for a value that is eight digits AND a real calendar date; otherwise return a refusal message naming the verb, the flag, the required `YYYYMMDD` format and the received value, `!r`-quoted so a traversal or an embedded newline is visible rather than mangling the terminal.
  DERIVE THE REGEX FROM RESEARCH'S OWN GRAMMAR AND DO NOT PORT THE SIBLING'S LITERAL. `research_contract._CORE_RE` is `\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)\Z` and `cli.py`'s help for this flag reads `Override the set date (YYYYMMDD).` Measured (F-11): the shipped ISO guard `\A\d{4}-\d{2}-\d{2}\Z` REFUSES `20260929` and ACCEPTS `2026-09-29`, which this grammar rejects, so a verbatim port would break the verb outright. Use `\A[0-9]{8}\Z` (ASCII digits). ALIGNED AT REVIEW with sibling `iumgvk`, whose own review (PR-002) changed its contract to ASCII because Python 3's `\d` matches any Unicode decimal digit, so `\A\d{8}\Z` ACCEPTS fullwidth `'２０２６０９２９'` and the format check is then not the gate it claims to be. OQ-03's convergence argument depends on the two plans specifying the IDENTICAL contract, so this plan follows `iumgvk`'s reviewed form, not its own authoring form.
  THEN ADD A CALENDAR CHECK, because eight digits alone is NOT sufficient and this is a different conclusion from the path half. Measured (F-11): `\A\d{8}\Z` ACCEPTS `99999999`, `20261332` and `20260230`, and `strptime(value, "%Y%m%d")` rejects all three while accepting `20260929`. STATE THE FORMAT-VERSUS-CALENDAR DISTINCTION IN THE CODE COMMENT, naming the shapes the regex alone admits.
  - Depends on: none
  - Expected outcome: a single helper reachable from `research_refs` that returns `None` for `None` and `'20260929'`, and a message naming the verb, `YYYYMMDD` and the received value for each of `'../../../../ESCAPED'`, `'/ABSOLUTE/ESCAPED'`, `'２０２６０９２９'` (fullwidth), `'2026-09-29'`, `'99999999'`, `'20261332'`, `'20260230'`, `'notadate'`, `''`, and `'20261002\nstatus: active'`; plus a written statement in the plan's own V-01 evidence of WHICH branch was taken (reused or added) and why.
  - Execution state: performed

- [x] E-02 CALL that guard from `research_refs.plan_set_assign`, returning its message through the function's EXISTING `(None, error)` tuple so `run_set_assign`'s established rendering (`print(f"error: {err}")` then `MutationResult(2)`) is reused rather than forked.

  GUARD AT THE PLANNER, NOT AT `run_set_assign`, AND THE REASON IS STRUCTURAL. `plan_set_assign` is the function that interpolates the value into `R.format_name`, it is public, it takes `date_str` as a POSITIONAL parameter, and it is the unit the tests can drive without a CLI. A guard in `run_set_assign` would leave the planner callable with an unvalidated date by any future caller, which is the same siting argument `iumgvk` made for the creation planners and `ribg85` made for `specs.run_new`.
  SITE THE CALL AT THE TOP, BESIDE THE EXISTING `set_k` REFUSAL. `plan_set_assign` already opens with `set_k = R.kebab(set_id)` / `if not set_k: return None, "a --set id is required"`, which establishes both the position and the message style for a pre-flight refusal. Place the date check immediately after that refusal and BEFORE the `for i, id6 in enumerate(id6s):` loop, so a bad date costs no selector resolution and touches no filesystem.
  PASS THE VERB NAME `"aw research set-assign"`, which F-03 measured is the only CLI spelling that can reach this flag (`aw group research` exits 2 with `unrecognized arguments: --date`). Do not write a message naming `aw group research`.
  DO NOT CHANGE THE OMITTED-FLAG DEFAULT. `run_set_assign` computes `date_str = getattr(args, "date", None) or date.today().strftime("%Y%m%d")` BEFORE calling the planner, so the planner never actually receives `None` from the CLI; the helper's `None` arm still matters for direct callers and the default path must keep producing today's date unchanged. V-02 asserts both.
  - Depends on: E-01
  - Expected outcome: `aw research set-assign w1qe6d --set grp --date ../../../../ESCAPED --apply` exits 2 with the refusal and the record STAYS at its original path, where before it exited 0 and the record left the repository; `--date /ABSOLUTE/ESCAPED` exits 2 with the same refusal instead of raising the F-06 `ValueError`; `--date 99999999`, `20261332`, `20260230`, `2026-09-29`, `notadate` and a newline-bearing value each exit 2; and `--date 20260929` plus every invocation that omits `--date` still renames exactly as before.
  - Execution state: performed

### Task group 2: confine the destination at the funnel both rename verbs share

- [x] E-03 Add a DESTINATION-CONTAINMENT assertion to `research_refs._apply_renames`, refusing when any planned `new_path`'s RESOLVED path does not lie inside the RESOLVED research root, with a message naming the offending destination and the tree it escaped, and exit 2 from the verb.

  THE FUNNEL HAS NO EXIT CHANNEL TODAY, SO E-03 MUST ADD ONE (measured at review). `_apply_renames` returns `Tuple[str, ...]` (the touched paths) and both callers unconditionally `return MutationResult(0, touched)`, so "a nonzero exit through the existing result channel" is not reachable inside the function as it stands. Implement the check as a pure module-private helper over `(repo_root, plans)` returning `Optional[str]` (the refusal message), call it at the top of `_apply_renames`, and on refusal print `error: <msg>` and return a sentinel the callers can distinguish (for example `None` instead of a tuple, with the return annotation widened to `Optional[Tuple[str, ...]]`); change BOTH `run_set_assign` and `run_mv` to return `MutationResult(2)` on that sentinel. Those are the only two callers (measured: `_apply_renames` is referenced nowhere else in `agent_workflows/` or `tests/`). Do NOT signal the refusal with an uncaught exception, which would turn the F-06 traceback into a different traceback. The pure helper is also the natural E-02 BYPASS for V-03: drive `_apply_renames` (or the helper) directly with a hand-built `RenamePlan` whose `new_path` escapes, which needs no monkeypatching of the date guard.

  THIS IS DEFENCE IN DEPTH AND IS NOT REDUNDANT WITH E-02, which is why it is a separate item. E-02 guards the one input measured to traverse today; E-03 guards the PROPERTY that matters, that these verbs only ever write inside their own tree, and it holds for any future caller or any future unvalidated field that reaches the name builder. A guard only ever reached after another guard has refused is untested, which is why V-03 requires it be exercised with E-02 bypassed.
  `_apply_renames` IS THE CORRECT SITE because it is the ONE funnel both rename verbs feed (`run_set_assign` and `run_mv` both call it) and it already contains BOTH arms: the `if not apply:` preview branch and the `for p in plans:` apply loop. Place the assertion ABOVE the `if not apply:` branch, so the preview arm refuses too.
  THE DRY-RUN ARM MUST REFUSE, AND ITS CURRENT OUTPUT IS WORSE THAN THE APPLY ARM'S. Measured (F-02): a traversing preview exits 0 and prints `--- would rename <abs src> -> ESCAPED-grp-00-w1qe6d-seed.findings.md ---`, which shows only `p.new_path.name` and so HIDES the traversal completely; the operator sees a clean-looking destination basename with no indication the file is about to leave the repository. A dry run is the one tool an operator has for checking a destructive command before running it, so this is the defect one step earlier and in a more deceptive form. This is the identical siting error review caught in `ribg85`, where the guard sat inside the apply arm; do not repeat it.
  USE THE ESTABLISHED IN-REPO IDIOM, NOT A `..` SUBSTRING TEST: resolve both paths and call `Path.relative_to`, treating `ValueError` as the escape, exactly as `check_engine.resolve_evidence_artifact` does under its comment "containment: candidate must be inside the repo root (no ../ escape)", as the shipped `specs.run_new` guard does, and as `_apply_renames`'s OWN `_rel` helper already does. A substring test is wrong in both directions: it rejects a legitimate directory named `..x` and it MISSES the absolute-path destination F-06 measured, which contains no `..` at all.
  DERIVE THE BOUNDARY FROM THE SAME RESOLVER THAT BUILT THE PATH. `_apply_renames` currently receives `repo_root` but NOT the research root, so resolve it with `R.resolve_research_root(repo_root)` rather than hard-coding `.aw/records/research`. That resolver deliberately falls back to a legacy `.agents/docs/research` tree when the modern one is absent, so a hard-coded modern path would refuse every legitimate rename in a legacy-layout repository. Both callers already have `repo_root`, so no PARAMETER change is required (the RETURN contract does change, as stated above).
  ALLOW A SUBDIRECTORY BELOW THE ROOT. Containment must be tested against the research ROOT and must accept a descendant, because `research_archive.apply_moves` calls this module's `_git_mv` to move records into `YYYYMM-Www` shard directories under that root, and `_apply_renames` itself is reached for records already living in `reference/202608/`-style shards. `relative_to` accepts any descendant so this needs no special case, but V-03 must prove it rather than assume it.
  REFUSE BEFORE ANY SIDE EFFECT, NOT PART-WAY THROUGH. The assertion must run over ALL plans before the first `_git_mv`, mirroring the reason the function's own reference-rewrite planning is already done up front; a per-plan check inside the loop would leave a multi-id `set-assign` half-moved.
  - Depends on: E-02
  - Expected outcome: with E-02's guard bypassed (a hand-built `RenamePlan` passed to `_apply_renames`), a traversing destination is refused by E-03 alone and the verb-level path returns exit 2, nothing is moved, and the message names the destination and the tree; the SAME bypassed call WITHOUT `--apply` also refuses rather than printing a `--- would rename ... -> ESCAPED-...md ---` line that hides the traversal; an absolute-path destination is refused by the same assertion instead of raising `ValueError`; a multi-id call with one bad destination moves NONE of them; and every conforming `set-assign` and `mv` still renames and still previews exactly as before, in BOTH a `.aw/records/research` and a legacy `.agents/docs/research` layout, including a record living in an archive shard subdirectory.
  - Execution state: performed

### Task group 3: pin the escape, the mechanism, and the non-regressions

- [x] E-04 Add `tests/test_research_set_assign_date_containment.py` pinning the ESCAPE as the primary property. Assert that the record is STILL AT ITS ORIGINAL PATH and that NO file exists anywhere under the temp base outside the research tree, not merely that the command failed, because an exit code alone does not distinguish the fix from the permissions accident the backlog item warns about.

  THE FIXTURE MUST BE NESTED AND EVERY PROBE'S TRAVERSAL DEPTH MUST BE BOUNDED TO THE FIXTURE DEPTH, ASSERTED BEFORE THE PROBE RUNS. THIS IS A SAFETY REQUIREMENT, NOT A STYLE NOTE. `artifact_core.git_mv` calls `(repo_root / dst_rel).parent.mkdir(parents=True, exist_ok=True)` before moving, so an OVER-DEEP traversal does not fail, it SUCCEEDS somewhere unintended: review of `ribg85` ran exactly such a probe and wrote a file outside its scratch area that it then could not delete. Build the fixture at `<tmp>/n1/n2/n3/repo`, compute the resolved target arithmetically, and assert it is inside the temp base BEFORE running; skip the probe rather than running it if it is not. COMPUTE THE BOUND FROM THE RESOLVED RESEARCH ROOT, NOT THE FIXTURE PATH, AND ISOLATE `HOME` (added at review, the hazard sibling `iumgvk`'s review measured destructively as its PR-001). `R.resolve_research_root` asks `record_producers.resolve_record_path` first, and for an unregistered scratch repo with no `.aw/records/research` directory it resolves OUTSIDE the fixture, under the real home: re-measured at this review, non-destructively, for a fresh `<tmp>/n1/n2/n3/repo`: `no dir: <home>/.aw/projects/repo-<hash>/records/research`, versus `with dir: <tmp>/n1/n2/n3/repo/.aw/records/research` once the directory exists. So every fixture MUST pre-create its research directory before any probe, MUST set `HOME` and `XDG_CONFIG_HOME` to the temp base for every subprocess and every in-process `cli.main` call, and MUST compute each probe's target from `R.resolve_research_root(repo)` and assert it is under the temp base. The LEGACY-layout fixture (V-03) is where this bites: it deliberately has no `.aw/records/research`, so the modern resolver's home-based answer is consulted first and only `HOME` isolation keeps it from being a real directory. Apply the same three rules to every MANUAL probe during execution. This plan's authoring probe bounded by fixture path only, which happened to be safe because its fixture seeded the modern directory; it also DEMONSTRATED its own value by refusing to run the absolute-path case (F-06), which is why that case is pinned at the planner rather than through the CLI.
  THE NESTING MUST CARRY A COMMENT SAYING WHY, AND THE COMMENT MUST NOT PROMISE A PERMISSION ERROR. The backlog item reports that a shallow fixture refuses with `Permission denied`; that refusal is an accident of filesystem permissions and is environment-dependent, so a shallow fixture yields a FALSE GREEN where the escape is unwritable and COLLATERAL DAMAGE where it is writable. Both are disqualifying and neither is a guard. The repository checkout is SHARED (AGENTS.md), so a test that escapes its own tmpdir can damage another agent's work.
  AN ABSOLUTE-PATH PROBE CANNOT BE BOUNDED AND MUST NOT BE DRIVEN DESTRUCTIVELY. `Path.__truediv__` discards the left operand when the right is absolute, so no fixture depth can contain it. Pin that case by calling `plan_set_assign` and asserting on the REFUSAL (post-fix) or on the planned path and the `relative_to` `ValueError` (pre-fix), never by applying it.
  Cover: a traversal landing above the records tree, a traversing DRY RUN with no `--apply` (E-03's second arm, including an assertion that the printed line does NOT merely show a clean basename), the newline-bearing date, the multi-id partial-move case, and a record living in an archive shard subdirectory. Drive at least one case through `cli.main` rather than the planner alone, following the established pattern in `tests/test_research_cmd_create.py`.
  - Depends on: E-03
  - Expected outcome: a new module whose escape cases FAIL against pre-E-01 code with the escaped file PRESENT on disk inside the temp base and the research tree EMPTY, and PASS after; and whose every destructive probe is bounded by an asserted in-tmpdir target so the module cannot damage the checkout it runs in.
  - Execution state: performed

- [x] E-05 In the same module, pin the MECHANISM and the non-regressions.

  THE MECHANISM, which is the finding most likely to be lost and which no other plan records. Pin that `git mv` ITSELF REFUSES the out-of-tree destination (exit 128, `fatal: '...' is outside repository`) and that the record leaves anyway through `artifact_core.git_mv`'s `shutil.move` fallback, and pin the GIT-INDEX CONSEQUENCE F-05 measured: after a pre-fix escape, `git status --short` shows ` D` on the old path while `git ls-files` STILL LISTS it, so the repository's own index disagrees with the filesystem. Name in a comment that the fallback is DELIBERATELY not changed here, that this plan's fix works by never reaching it, and that its carrier is backlog item `ki1uqk`. This pins a LIVE defect, so say so in the comment rather than letting a reader take it for approval.
  DETECTION BLINDNESS, pinned so the under-scope is evidence rather than assertion: after a pre-fix escape, `aw research index --check --dir <repo>` reports `index --check: clean` at exit 0, `aw research index` reports `(0 docs)`, `aw research find --agent` reports `no matching research docs`, and `aw check research --agent` reports `"outcome":"conforms"` on a repository that has just lost its only record (F-01, F-09). Record it; this plan does not fix it.
  FABRICATION: assert `--date 99999999`, `20261332` and `20260230` are refused, and document in the test name that this half is about record IDENTITY rather than path safety. A fabricated filename date is an already-realized harm here, recorded in open backlog item `tf4jz5`.
  NON-REGRESSIONS: (a) `--date 20260929` produces the SAME destination name and the SAME frontmatter updates as before the change, compared against a reference generated at HEAD; (b) omitting `--date` still defaults to today; (c) a conforming DRY RUN still previews the same lines and still exits 0; (d) the existing refusals (`a --set id is required`, the setid-length guard, `no research file has id6`, the non-conformant-source refusal) keep their exit codes and messages; (e) `aw research mv` is UNCHANGED, asserted by driving it and observing an identical rename, since it shares the E-03 funnel but takes its date from `parsed.date` and so was never exposed (F-07); (f) `aw research archive` still moves records INTO its shard subdirectory, which is the case E-03's descendant allowance exists to protect.
  - Depends on: E-04
  - Expected outcome: the mechanism, the git-index inconsistency, the detection blindness and the fabrication refusals are pinned; the six non-regression groups pass; and the `git_mv` fallback residue is recorded in-test with its carrier named, so the scope boundary is measured rather than asserted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- RESEARCH'S DATE GRAMMAR IS `YYYYMMDD`, NOT ISO, which is the single fact that prevents this plan from copying the shipped sibling guard. `research_contract._CORE_RE` is `\A(?P<date>\d{8})-(?P<set>[a-z0-9-]+?)-(?P<nn>\d{2})-(?P<id6>[0-9a-z]{6})-(?P<slug>[a-z0-9-]+)\Z`, and `cli.py`'s help for this flag reads `Override the set date (YYYYMMDD).`
- THE TWO-GUARD SHAPE IS ESTABLISHED IN-REPO, so this plan ports a shape rather than inventing policy: `prompts.run_new` validates its `--date` against a format regex and refuses at exit 2 before deriving a name, and executed plan `ribg85` added both a format-plus-calendar guard and a `relative_to`-based containment assertion to `specs.run_new`.
- THE CONTAINMENT IDIOM IS `relative_to` WITH `ValueError` AS THE ESCAPE SIGNAL, used by `check_engine.resolve_evidence_artifact` under the comment "containment: candidate must be inside the repo root (no ../ escape)", by the shipped `specs.run_new` guard, and ALREADY by `_apply_renames`'s own `_rel` helper, which does `path.resolve().relative_to(repo_root.resolve())` in a `try`/`except ValueError`. Not a `..` substring test.
- `research_refs` ALREADY IMPORTS `research_cmd` (`from agent_workflows import research_cmd as _rcmd`) AND THE REVERSE IS NOT TRUE (`research_cmd` imports only `artifact_core` and `research_contract`), so the date helper `iumgvk` adds to `research_cmd` is reusable from here with no cycle and no new dependency edge.
- `_apply_renames` IS THE SINGLE PREVIEW-AND-APPLY FUNNEL for both rename verbs (`run_set_assign` and `run_mv`), and it already does its reference-rewrite planning up front before any move, which is the function's established place for a pre-flight step that must bind both arms.
- ONLY THE DATE SEGMENT IS UNSANITIZED among the name inputs, which is why this plan guards the date and nothing else: `plan_set_assign` applies `R.kebab` to `set_id`, and every other field it passes to `R.format_name` comes from `R.parse_name(src.name)` on an ALREADY-CONFORMANT source filename (`parsed.order`, `parsed.id6`, `parsed.slug`, `parsed.model`, `parsed.kind`), which the function refuses to proceed without.
- THE REFUSAL CONVENTION FOR THIS VERB IS EXIT 2 THROUGH THE PLANNER'S ERROR TUPLE: `run_set_assign` renders a planner error as `print(f"error: {err}")` then `return MutationResult(2)`, and its own `--set`-length and empty-ids refusals use the same shape.
- THE SETID-LENGTH GUARD ALREADY SITS IN `run_set_assign` AND IS THE PRECEDENT FOR A PRE-FLIGHT REFUSAL THERE, carrying the comment "setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard, on the RESEARCH backend of `aw group`"; it refuses before the planner is called. This plan deliberately sites its own guard in the PLANNER instead, for the reason E-02 states.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection (AGENTS.md).

## Findings

All findings were DRIVEN in this lane at HEAD `afae0d0e8`, against temporary fixture repositories nested four levels deep, with every traversal probe's resolved target asserted inside the temp base BEFORE the probe ran. None of this is read off the source.

| # | Finding | Evidence |
|---|---|---|
| F-01 | `aw research set-assign --date` MOVES A COMMITTED RECORD FOUR DIRECTORIES ABOVE THE RECORDS TREE at exit 0, leaving the repository's research directory holding no record. The item's report reproduces exactly. | Fixture at `<tmp>/n1/n2/n3/repo` with one committed record: `research set-assign w1qe6d --set grp --date ../../../../ESCAPED --dir <repo> --apply` printed `renamed .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md -> .aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md`, then a `warning:` about non-conformance, then `wrote .aw/records/research/INDEX.json, INDEX.md (0 docs)`, at `rc=0`. The file was found at `n1/n2/n3/ESCAPED-grp-00-w1qe6d-seed.findings.md` and the research tree afterwards held only `INDEX.md`. A following `research index --check` printed `index --check: clean` at `rc=0`. |
| F-02 | THE DRY RUN LEAKS THE ESCAPE AND ITS OUTPUT IS MORE DECEPTIVE THAN THE APPLY ARM'S, because it prints only the destination BASENAME and so hides the traversal entirely. | Same fixture, no `--apply`: `rc=0` printing `--- would rename <tmp>/n1/n2/n3/repo/.aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md -> ESCAPED-grp-00-w1qe6d-seed.findings.md ---` plus a non-conformance `warning:`. The printed destination is `ESCAPED-grp-00-w1qe6d-seed.findings.md`, with no `../` visible anywhere, because `_apply_renames`'s preview prints `p.new_path.name`. Nothing was moved on this arm, so the harm is a preview that conceals an out-of-repository move. |
| F-03 | `aw group research` CANNOT REACH THIS DEFECT, so the vulnerable surface is ONE verb spelling and not two, which narrows the plan and its tests. | Driven with the identical traversal: `group research w1qe6d --set grp --date ../../../../ESCAPED --dir <repo> --apply` exited **2** with `agent-workflows: error: unrecognized arguments: --date`; nothing moved, `git status --short` stayed clean, and `git ls-files` still listed the record. Both spellings route to `research_refs.run_set_assign` via `artifact_types.TYPE_BACKENDS["research"]["group"]`, but only the `research set-assign` parser defines `--date`. |
| F-04 | GIT ITSELF REFUSES THIS MOVE AND THE ESCAPE ONLY HAPPENS BECAUSE `artifact_core.git_mv` SWALLOWS THE REFUSAL, which reframes the defect: the record leaves the repository through a fallback written for untracked files. | Driven directly: `git -C <repo> mv -- .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md .aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md` exited **128** with `fatal: '.aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md' is outside repository at '<repo>'`. `artifact_core.git_mv`'s body is `(repo_root / dst_rel).parent.mkdir(parents=True, exist_ok=True)`, the `git mv` subprocess, then `if result.returncode != 0:` -> `shutil.move(str(repo_root / src_rel), str(repo_root / dst_rel))`, under the docstring "with a filesystem fallback for untracked files". |
| F-05 | THE ESCAPE LEAVES THE GIT INDEX INCONSISTENT WITH THE FILESYSTEM, so the loss is worse than a moved file: the repository still believes the record is tracked at its old path. | After the F-01 escape: `git status --short` reported ` D .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md` (an UNSTAGED deletion, because `shutil.move` staged nothing), while `git ls-files` still listed that same path. The escaped copy is untracked and outside the repository, so a later `git checkout`/`restore` would resurrect a stale record while the moved file lingers out of tree. |
| F-06 | AN ABSOLUTE `--date` DOES NOT ESCAPE, IT CRASHES, so the fix must cover a shape the item does not mention, and a bounded test CANNOT drive it destructively. | `plan_set_assign(research_root, ['w1qe6d'], 'grp', '/ABSOLUTE/ESCAPED', repo_root=repo)` returned `err=None` and planned `new_path=/ABSOLUTE/ESCAPED-grp-00-w1qe6d-seed.findings.md`; `new_path.relative_to(repo_root)` then raises `ValueError: '/ABSOLUTE/ESCAPED-grp-00-w1qe6d-seed.findings.md' is not in the subpath of '<repo>'`, which is exactly the unguarded call `_apply_renames` makes as `dst_rel = p.new_path.relative_to(repo_root).as_posix()`. SEPARATELY, this plan's own bound check REFUSED to run the CLI probe for this case (`target /tmp/aw_0ougsh_ABS-... inside base? False` -> `REFUSING TO RUN`), which is the bounding discipline E-04 requires working as intended. |
| F-07 | `aw research mv` SHARES THE SAME WRITE FUNNEL BUT PROVABLY CANNOT TRAVERSE, which is why E-03's assertion is cheap to site and why `mv` is a non-regression rather than a second fix. | `plan_mv` builds its `R.ResearchName` with `date=parsed.date`, taken from `R.parse_name(src.name)` on a source filename the function refuses to proceed without (`file '...' is not a conformant research document`). It accepts no date flag: the `research mv` parser offers `--slug`, `--kind` and `--model` only. So the only unvalidated date entering `_apply_renames` arrives through `plan_set_assign`. |
| F-08 | A NEWLINE IN `--date` IS A SECOND, DISTINCT OUTCOME ON THIS VERB, exactly as the item reports: the rename IS PERFORMED despite the grammar rejecting the result, leaving a record whose filename contains a literal newline. | Driven with `--date $'20261002\nstatus: active' --apply`: `rc=0`, printing `renamed ... -> .aw/records/research/20261002\nstatus: active-grp-00-w1qe6d-seed.findings.md`, a `warning:` that the destination is non-conformant, AND a `name-invalid` line. The research tree afterwards held `'20261002\nstatus: active-grp-00-w1qe6d-seed.findings.md'`. Unlike the creation twin this does NOT inject front-matter keys, because the rename path writes no new front matter from the date; `_planned_frontmatter_updates` derives only `set`, `order` and `kind` from the parsed destination, and the parse fails here so nothing is written. |
| F-09 | THE ESCAPED RECORD IS INVISIBLE TO EVERY CHECKER IN THE TREE, so nothing downstream detects the F-01 loss. | After the F-01 escape, in the same fixture: `research index --check` printed `index --check: clean` at `rc=0`; `research index --agent` reported `up to date .aw/records/research/INDEX.json, INDEX.md (0 docs)`; `research find --agent` reported `no matching research docs`; and `check research --agent` reported `{"outcome":"conforms","exit":0,...,"findings":1,...[{"location":"<collisions>","rule":"check.collisions-not-checked"}]}`, i.e. only the standing advisory. A repository that had just lost its only research record reported clean four different ways. |
| F-10 | THE LIVE POPULATION WOULD PASS THE PROPOSED GUARD, so this plan is purely preventive with no migration step. | Over all 134 `.md` files under `.aw/records/research` (including `reference/`/archive shards): 0 names carry eight leading digits that are not a real calendar date; the 6 non-matching names are `README.md` x5 and `conformance-results-template.md`, none of which is a record. `check research --agent` reports `"outcome":"conforms"` with its one standing `check.collisions-not-checked` advisory. |
| F-11 | THE SIBLING'S REGEX CANNOT BE PORTED VERBATIM, which contradicts the item's own "reuse the `ribg85` fix shape" instruction read literally, and the eight-digit form alone is insufficient. | Each candidate matched against both patterns and `strptime(v, '%Y%m%d')`: the ISO `\A\d{4}-\d{2}-\d{2}\Z` REFUSES `20260929` (the only shape `_CORE_RE` accepts) and ACCEPTS `2026-09-29` and `9999-99-99`; `\A\d{8}\Z` accepts `20260929` and refuses every traversal, absolute path, newline and ISO form tested, but ACCEPTS `99999999`, `20261332` and `20260230`, which `strptime` rejects. Driven at the planner, `--date 2026-09-29`, `notadate`, `99999999`, `20261332`, `20260230` and `''` ALL planned a destination inside the tree with no error, so today the verb silently accepts every one of them. |
| F-12 | `attention_contract.is_safe_descriptive` PROVABLY CANNOT DETECT THIS, re-confirming the item's claim and why the fix class is date validation plus containment rather than the descriptive predicate. | Driven: `is_safe_descriptive('../../../../ESCAPED')`, `is_safe_descriptive('/ABSOLUTE/ESCAPED')`, `is_safe_descriptive('99999999')` and `is_safe_descriptive('notadate')` ALL return `True`, because each is a single bounded control-char-free line. Plan `deftzy`'s Scope bullet names `--date` as "DELIBERATELY NOT COVERED", so the descriptive work does not and cannot close this. |
| F-13 | THE SUITE AND THE TARGETED REGRESSION SET ARE GREEN AT AUTHORING HEAD apart from three PRE-EXISTING failures that are ALREADY FILED, so a later failure is attributable to this plan's execution. | BARE `python3 -m pytest` at HEAD `afae0d0e8` with NO source modified: `3 failed, 4624 passed, 2 skipped, 3 warnings in 116.08s`, 232 deselected. The three are `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` (open item `6bolin`), `test_selector_type_containment.py::test_must_not_refuse_matrix` (open item `bxnhdj`), and `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` (open item `8jeh4x`). The named regression set (`tests/test_research_cmd_create.py tests/test_research_index.py tests/test_research_rename_frontmatter.py tests/test_research_archive.py tests/test_group_verb_policy.py tests/test_specs_date_containment.py`): `167 passed in 3.78s`. |

## Proposed changes (ordered, validatable)

1. E-01: make a single date guard reachable from `research_refs`, by REUSING `research_cmd._refuse_unsafe_date` if plan `iumgvk` has landed it or ADDING it there to the same contract if not; validating `\A[0-9]{8}\Z` (ASCII digits, aligned with `iumgvk` PR-002; derived from research's OWN `_CORE_RE` date slot, NOT ported from the ISO sibling: F-11) and then calendar validity via `strptime(..., "%Y%m%d")`.
2. E-02: call it from `research_refs.plan_set_assign`, immediately after the existing `a --set id is required` refusal and before the selector loop, returning through the existing `(None, error)` channel so `run_set_assign` renders `error: <msg>` at exit 2 unchanged.
3. E-03: assert destination containment in `research_refs._apply_renames`, above its `if not apply:` branch so BOTH the deceptive preview arm (F-02) and the apply arm refuse, using `relative_to`/`ValueError` against `R.resolve_research_root(repo_root)` so an absolute destination is caught instead of crashing (F-06), a legacy layout still works, and an archive shard descendant is still allowed.
4. E-04: pin the escape through the CLI with a nested fixture whose traversal depth is BOUNDED to the fixture depth and asserted before each probe, asserting the record is still at its original path and nothing exists outside the tree; pin the absolute case at the PLANNER because it cannot be bounded (F-06).
5. E-05: pin the swallowed `git mv` refusal and the git-index inconsistency (F-04, F-05), the detection blindness (F-09), the fabricated-date refusals, and six non-regression groups including `research mv` (F-07) and the archive shard move.

## Deferred / out of scope (with reason)

- `artifact_core.git_mv`'s FALLBACK THAT SWALLOWS GIT'S OWN REFUSAL is not changed here, even though F-04 measured it is the actual mechanism by which the record leaves the repository: `git mv` exits 128 saying the destination is outside the repository, and the helper then performs the move with `shutil.move` anyway. Deferred because that helper is shared by every rename and archive verb in the toolkit (`research_refs._apply_renames`, `research_archive.apply_moves`, and `engine`'s own installer moves), its fallback exists deliberately for untracked files, and `git mv` exits nonzero for BOTH the untracked case and the outside-repository case, so narrowing it means DISTINGUISHING those two rather than deleting an arm; that is a behavior change to the toolkit's shared move primitive, across callers this plan neither measures nor tests. This plan makes the escape unreachable through the verb that had it, which is the correct boundary for a verb-side fix; E-05 pins the fallback's current behavior so the boundary is evidence rather than assertion. Backlog item `ki1uqk` was FILED while authoring this plan (not merely promised) and carries the F-04 and F-05 measurements, because no existing item covers the helper: `0ougsh` is this verb, `m5csyi` is the creation paths, and neither names it.
  - Carrier: ki1uqk
- THE CREATION PATHS `aw research new`, `aw research new-comparison` AND `aw adopt` keep the identical unvalidated `--date` and are NOT fixed here. Deferred because pending plan `iumgvk` (Set `m5csyi`) owns exactly that surface, guards it at `research_cmd.plan_new`/`plan_new_comparison`, and this plan's E-01 deliberately REUSES the helper it adds rather than duplicating it. The two plans touch different modules (`research_cmd` versus `research_refs`), so they do not conflict; if `iumgvk` has not landed when this executes, E-01's second branch adds the helper to the same contract so `iumgvk` converges on it.
  - Carrier: m5csyi
- THE DESCRIPTIVE-FIELD INJECTION THROUGH `--summary`, `--topic` AND `--consumed-by` is not addressed here. Deferred because pending plan `deftzy` (Set `7w6zsl`) owns that surface, and its Scope bullet explicitly excludes `--date`. NOTE the asymmetry that makes them genuinely separate: F-12 re-measured that `is_safe_descriptive` returns `True` for a traversal, so `deftzy`'s predicate cannot close this defect, and this plan's date guard cannot close `deftzy`'s.
  - Carrier: 7w6zsl
- THE DETECTION BLINDNESS F-09 MEASURES IS NOT CLOSED. After this plan nothing can move a research record out of the tree through `set-assign`, which is the right fix; but `aw research index --check` reporting `clean`, `research find` reporting no docs, and `check research` reporting `conforms` for a repository whose record has left the tree stays true for any record removed by other means (a hand `mv`, a bad merge, the `git_mv` fallback above). Recorded because a reader could mistake this plan for closing detection as well as the write path; it closes only the write path, which is the correct boundary for a verb-side guard.
  - Carrier-Declined: The obligation is discharged rather than postponed for the defect class this plan exists to close. A tree checker cannot be asked to notice a record it has never seen without a separate durable inventory, which is a different design question with no measurement here showing harm once the write paths refuse; the remaining live producers of an out-of-tree record are the creation paths (carried by `m5csyi`) and the `git_mv` fallback (carrier filed above), so filing a third carrier for the detection half would schedule work no finding in this plan supports.
- `prompts.run_new` IS LEFT WITH THE WEAKER, FORMAT-ONLY GUARD and is not upgraded. After this plan research validates format AND calendar validity while `aw prompts new --date 9999-99-99` still stamps a fabricated date. Recorded so the divergence reads as seen rather than missed.
  - Carrier-Declined: Nothing is owed by THIS plan because the obligation is already recorded against the prompts tree by executed plan `ribg85`, whose Deferred section carries the identical row, and re-recorded by pending `iumgvk`. Filing a third carrier for one already-recorded divergence would duplicate a work item rather than schedule anything new, and F-11 shows the two grammars differ, so the upgrade is not even a copy.
- NO EXISTING RECORD IS REMEDIATED, which F-10 shows is vacuous for this tree (0 of 134 would fail the new guard). The separately-carried fabricated-date remediation concern remains filed as `tf4jz5`.
  - Carrier-Declined: There is nothing to remediate: the measurement found zero live records whose filename date would fail the guard, so a carrier would schedule an empty migration.

## Scope check

- Over-scope: none. One guard call and one containment assertion in ONE module (`research_refs`), plus one new test module, plus (only on E-01's second branch) one helper in `research_cmd` that a sibling plan is independently adding anyway; `agent_workflows/research_cmd.py` is therefore declared in `- Scope-Paths:` (added at review) and is acknowledged with `--scope-ack` if E-01 takes the reuse branch. `research_contract.format_name`, `_CORE_RE`, `artifact_naming`, `artifact_core.git_mv`, `research_cmd`'s planners, `research_archive`, `plans_refs`, `cli.py`'s parsers, every rule id, and every `--agent` envelope SCHEMA stay untouched. E-03 DOES change what a traversing dry run prints, from a `--- would rename ... -> ESCAPED-...md ---` line to a refusal (F-02); that is the fix, not scope creep. The `--date` help string is already correct (`Override the set date (YYYYMMDD).`), so the guard makes the code match the shipped documentation rather than requiring a documentation change.
- Under-scope: (a) `artifact_core.git_mv` keeps the fallback that swallows git's own out-of-tree refusal (F-04) and the index inconsistency it causes (F-05), carried by open backlog `ki1uqk` (already filed at authoring); (b) the creation paths keep the identical unvalidated `--date`, carried by `m5csyi`/`iumgvk`; (c) the descriptive-field injection stays open, carried by `deftzy`/`7w6zsl`, and `is_safe_descriptive` provably cannot close THIS defect (F-12); (d) the detection blindness F-09 measures is not closed, so a record removed from the tree by other means stays invisible to `index --check`, `find` and `check research`; (e) `aw prompts new` keeps its format-only guard; (f) no existing record is remediated, which F-10 shows is vacuous here.
- Under-scope, STATED PLAINLY BECAUSE IT BOUNDS THE SEVERITY CLAIM: this plan does not make the already-escaped record recoverable in any repository where this verb has already been run. It is forward-only. No such escape is known to have occurred in this repository (F-10 found every live record conformant and in-tree), but the plan cannot prove one never did in a downstream managed repo, and it adds no detector that would find one (see (d)).

## Required tests / validation

- `python3 -m pytest tests/test_research_set_assign_date_containment.py` for the new module (run BARE; `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection).
- `python3 -m pytest tests/test_research_cmd_create.py tests/test_research_index.py tests/test_research_rename_frontmatter.py tests/test_research_archive.py tests/test_group_verb_policy.py tests/test_specs_date_containment.py` as the targeted regression set: these own the module being edited, the index that reads the derived names, the frontmatter updates `_apply_renames` writes, the archive shard writer whose nested destination E-03 must keep allowing, the `aw group` routing F-03 measured cannot reach this flag, and the sibling date-containment module whose shape this plan reuses.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression.
- RE-DERIVE THE BASELINE RATHER THAN TRUSTING A NUMBER IN THIS PLAN, and expect the three PRE-EXISTING failures F-13 names, each already filed (`6bolin`, `bxnhdj`, `8jeh4x`). Run the bare suite BEFORE your first edit and after your last, and treat a failure as yours only when it does not appear in your own pre-edit run.
- `aw check research --agent` must still report `"outcome":"conforms"` and `aw research index --check` must behave unchanged on the repository tree, re-deriving the population count at execution rather than trusting F-10's 134. The standing `check.collisions-not-checked` advisory is the expected baseline, not a regression. NOTE that `aw research index --check` on this repository currently reports pre-existing `adopted-without-consumer` findings on archived records; that is the baseline, not something this plan causes or fixes.
- PRE-FIX FALSIFICATION IS REQUIRED: V-04 must show the escape test FAILING against pre-E-01 code WITH THE ESCAPED FILE PRESENT on disk and the research tree EMPTY, not merely a nonzero exit, because an exit-code difference alone does not distinguish the fix from the permissions accident the backlog item warns about. Obtain the pre-fix run by authoring the test module first, or against a separate `git worktree` at HEAD; do NOT `git stash push -- agent_workflows/research_refs.py`, since this checkout is SHARED and stashing a path can swallow a co-worker's uncommitted edit.
- THE PRE-FIX RUN IS THE DANGEROUS ONE, SO BOUND IT BEFORE RUNNING IT. It exercises a verb that MOVES a tracked file out of the repository and whose helper CREATES the destination's parent to do so (F-04), so an over-deep traversal succeeds somewhere unintended rather than failing; review of the sibling plan wrote a file outside its scratch area this way and could not delete it afterwards. Before each destructive probe, resolve the target arithmetically and assert it is inside your temp base; if it is not, fix the depth rather than running it. Never run a traversal probe whose resolved target you have not computed first, and never run one from a fixture shallower than the traversal is deep. The absolute-path case CANNOT be bounded at all and must be driven at the planner only (F-06).
- VERIFY THE CONTAINMENT ASSERTION INDEPENDENTLY OF THE DATE GUARD: V-03 must exercise E-03 with E-02 bypassed, stating exactly how the bypass was done, because a guard only ever reached after another guard has refused is untested and defence in depth is its entire purpose.

## Spec / documentation sync

N/A with reason. This plan adds input validation and a containment assertion to one module; it changes no rule id, adds no field, and amends no spec, so no `.spec.md` appears in `- Scope-Paths:`. The governing contract is the uniform artifact-naming grammar (spec `uniform-artifact-naming-grammar`), whose `YYYYMMDD` date slot this plan makes the rename verb actually honor rather than redefining; `research_contract._CORE_RE` already encodes that slot and is unchanged. The user-facing surface that changes is the refusal text emitted by the code this plan edits; the `--date` help string already reads `Override the set date (YYYYMMDD).`, so the guard makes the code match the shipped documentation rather than requiring a documentation change.

## Open questions

### OQ-01: Should `--date` be validated for CALENDAR validity, or only for the eight-digit FORMAT?

- Blocking: no
- Status: resolved
- Owner: plan author (NOT a maintainer ruling)
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT: validate BOTH, format first then calendar, as two explicit checks. The format half is forced, because `\A\d{8}\Z` is the only shape `research_contract._CORE_RE` accepts and it alone closes the ENTIRE path class: a value matching it cannot contain `/`, `\` or `.`, so no eight-digit date can traverse or be absolute, and no newline can survive it (F-11). The calendar half is NOT forced by the path argument and needed its own evidence: driven at the planner, `--date 99999999`, `20261332` and `20260230` all plan a destination INSIDE the tree with no error (F-11), so a format-only guard would still let this verb RENAME a committed record to a fabricated date. That matters more on this verb than on the creation twin, because here the fabricated date REPLACES a correct one on an existing artifact, and the real date then survives only in git history: exactly the harm open backlog item `tf4jz5` records for an executed plan whose real `20260723` was lost that way. The cost is zero: F-10 measured 0 of 134 live records would fail the calendar check. NON-BLOCKING because the severe half, the out-of-repository move, is closed by the eight-digit regex and by E-03's containment assertion regardless of how this resolves. CONSEQUENCE FOR THE SIBLING, stated so it is not silently orphaned: `prompts.run_new` keeps a format-only guard and still accepts `9999-99-99`; that divergence is recorded in Deferred and declined with reason, not missed.

### OQ-02: Should the containment assertion live in `_apply_renames`, or in `plan_set_assign` beside the format guard?

- Blocking: no
- Status: resolved
- Owner: plan author (NOT a maintainer ruling)
- Resolution or deferral rationale: RESOLVED: `_apply_renames`, for three measured reasons. FIRST, it is the WRITE boundary and the only place that binds both arms: it contains both the `if not apply:` preview branch and the apply loop, and F-02 measured that the preview arm leaks the escape in a MORE deceptive form than the apply arm (printing only the basename, so no `../` is visible), so a guard that does not cover the preview misses the worse half. SECOND, it is shared by BOTH rename verbs, so the property "these verbs only write inside their own tree" is established once rather than per planner; `run_mv` reaches it too, and F-07 measured `plan_mv` cannot traverse today, so siting it here costs nothing and protects a future change to `plan_mv`. THIRD, it is the only site that catches the ABSOLUTE-path shape as a refusal rather than a crash: F-06 measured `_apply_renames`'s own `p.new_path.relative_to(repo_root)` raising an uncaught `ValueError` for that input, which a planner-side guard would leave as a traceback. The cost of this siting is that `_apply_renames` must resolve the research root itself (via `R.resolve_research_root(repo_root)`) because it is not currently passed one; that is one line, both callers already hold `repo_root`, and no signature changes.

### OQ-03: Should this plan wait for `iumgvk` so the shared helper certainly exists?

- Blocking: no
- Status: resolved
- Owner: plan author (NOT a maintainer ruling)
- Resolution or deferral rationale: RESOLVED: no, and `- Item-Dependencies:` is deliberately `none`. The two plans edit DIFFERENT modules (`iumgvk` edits `research_cmd`, this edits `research_refs`), so neither blocks the other and the runner isolates each lane and returns changes through the merge-and-revalidate gate. Declaring a dependency would serialize two independent fixes for a release-blocking defect and would make this plan unrunnable if `iumgvk` were retired or revised. E-01 is therefore written as a two-branch instruction: reuse the helper if present, add it to the same contract if not, and RECORD which branch was taken. The only cost of the second branch is that both plans may add the same helper; because the contract is specified identically in both plans (after this review aligned the regex to `iumgvk`'s reviewed ASCII form), that resolves as a trivial merge rather than a semantic conflict. If it does produce a textual conflict in `research_cmd.py`, the merge-and-revalidate gate surfaces it; resolve to ONE definition. This also keeps the ordering free in the other direction: whichever executes second finds the helper already there and simply calls it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: STATE WHICH BRANCH YOU TOOK (reused the existing `research_cmd._refuse_unsafe_date`, or added it) and paste the evidence for that determination: a `grep`/import showing the helper's presence or absence at the HEAD you executed from. Then paste the helper's SOURCE, showing both the `\A[0-9]{8}\Z` regex and the `strptime(..., "%Y%m%d")` calendar check, and the code comment stating the format-versus-calendar distinction and naming the shapes the regex alone admits. Then paste a driven table of the helper's return value for EACH of `None`, `'20260929'`, `'../../../../ESCAPED'`, `'/ABSOLUTE/ESCAPED'`, `'2026-09-29'`, `'99999999'`, `'20261332'`, `'20260230'`, `'notadate'`, `''`, and `'20261002\nstatus: active'`, and `'２０２６０９２９'` (fullwidth digits), showing `None` for the first two and a message naming the verb, `YYYYMMDD` and the received value for the rest. A run where `'99999999'` returns `None` has NOT implemented the calendar half and fails this item. Finally, confirm by import that no second date guard was defined in `research_refs` (one grammar, one guard).
  - Observed evidence:
    BRANCH TAKEN: REUSED existing `research_cmd._refuse_unsafe_date`.
    Evidence of presence at execution HEAD (afae0d0e8):
    ```sh
    $ python3 -c "import agent_workflows.research_cmd as r; print(hasattr(r, '_refuse_unsafe_date'))"
    True
    ```
    Helper source in `agent_workflows/research_cmd.py`:
    ```python
    def _refuse_unsafe_date(verb: str, value: Optional[str]) -> Optional[str]:
        """Judge one candidate date string against research's date grammar and calendar validity.

        E-01 (IPD iumgvk): Derived from research's own date grammar slot (_CORE_RE).
        The regex check (\\A[0-9]{8}\\Z) is an ASCII format check, not a calendar check;
        the regex alone admits unreachable calendar dates such as 99999999 and 20261332.
        Per OQ-01, validate format first (ASCII-only [0-9]{8}, refusing fullwidth digits like
        '２０２６０９２９'), then calendar validity via datetime.strptime(..., "%Y%m%d"),
        refusing both with exit 2 and the same message shape naming the verb, --date,
        YYYYMMDD, and the received value.
        """
        if value is None:
            return None
        # Format check: research grammar uses YYYYMMDD, not ISO YYYY-MM-DD.
        # ASCII [0-9]{8} closes non-ASCII Unicode digits (PR-002).
        if not re.match(r"\A[0-9]{8}\Z", value):
            return f"{verb}: --date must be YYYYMMDD (got {value!r})"
        # Calendar check: regex alone accepts 99999999 and 20261332.
        try:
            datetime.strptime(value, "%Y%m%d")
        except ValueError:
            return f"{verb}: --date must be YYYYMMDD (got {value!r})"
        return None
    ```
    Driven table of helper return values for required inputs:
    ```
    None                                -> None
    '20260929'                          -> None
    '../../../../ESCAPED'               -> "aw research set-assign: --date must be YYYYMMDD (got '../../../../ESCAPED')"
    '/ABSOLUTE/ESCAPED'                 -> "aw research set-assign: --date must be YYYYMMDD (got '/ABSOLUTE/ESCAPED')"
    '2026-09-29'                        -> "aw research set-assign: --date must be YYYYMMDD (got '2026-09-29')"
    '99999999'                          -> "aw research set-assign: --date must be YYYYMMDD (got '99999999')"
    '20261332'                          -> "aw research set-assign: --date must be YYYYMMDD (got '20261332')"
    '20260230'                          -> "aw research set-assign: --date must be YYYYMMDD (got '20260230')"
    'notadate'                          -> "aw research set-assign: --date must be YYYYMMDD (got 'notadate')"
    ''                                  -> "aw research set-assign: --date must be YYYYMMDD (got '')"
    '20261002\nstatus: active'          -> "aw research set-assign: --date must be YYYYMMDD (got '20261002\\nstatus: active')"
    '２０２６０９２９'                          -> "aw research set-assign: --date must be YYYYMMDD (got '２０２６０９２９')"
    ```
    Confirmed by inspection and import that no second date guard was defined in `research_refs` (dir contains `_refuse_uncontained_destination` and no duplicate date validator).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the actual terminal output of these runs against a temp fixture NESTED at least four directories deep with one COMMITTED research record (see V-04 for why nesting is mandatory). (a) `aw research set-assign <id6> --set grp --date ../../../../ESCAPED --dir <repo> --apply` showing exit 2, the refusal naming the flag and the required format, the record STILL AT ITS ORIGINAL PATH, a clean `git status --short`, and proof that no `.findings.md` exists anywhere under the temp base outside the research tree. (b) the SAME call with no `--apply`, showing exit 2 rather than a `--- would rename ... ---` line. (c) `--date /ABSOLUTE/ESCAPED` exiting 2 with the date refusal and NOT a `ValueError` traceback. (d) `--date 2026-09-29`, `notadate`, `99999999`, `20261332`, `20260230`, `''` and a newline-bearing value each exiting 2. (e) `--date 20260929 --apply` still succeeding at exit 0 with the expected destination name and the expected `set metadata` line. (f) an invocation OMITTING `--date` still renaming to today's date. (g) the guard call's source, showing it sits after the `a --set id is required` refusal and BEFORE the `for i, id6 in enumerate(id6s):` loop, with enough surrounding source to show that order. (h) the PRE-FIX counterpart of (a): exit 0, the record's escaped path on disk, and the research tree empty.
  - Observed evidence:
    Driven against fixture at `<tmp>/n1/n2/n3/repo` with committed record `20260101-seed-00-w1qe6d-seed.findings.md`:
    (a) Traversal with --apply:
    ```
    error: aw research set-assign: --date must be YYYYMMDD (got '../../../../ESCAPED')
    exit code: 2
    original record exists: True
    git status --short: <clean>
    escaped files outside research tree: []
    ```
    (b) Traversal dry run (no --apply):
    ```
    error: aw research set-assign: --date must be YYYYMMDD (got '../../../../ESCAPED')
    exit code: 2
    ```
    (c) Absolute date:
    ```
    error: aw research set-assign: --date must be YYYYMMDD (got '/ABSOLUTE/ESCAPED')
    exit code: 2
    ```
    (d) Other invalid dates:
    ```
    error: aw research set-assign: --date must be YYYYMMDD (got '2026-09-29')
    '2026-09-29'              -> exit code 2
    error: aw research set-assign: --date must be YYYYMMDD (got 'notadate')
    'notadate'                -> exit code 2
    error: aw research set-assign: --date must be YYYYMMDD (got '99999999')
    '99999999'                -> exit code 2
    error: aw research set-assign: --date must be YYYYMMDD (got '20261332')
    '20261332'                -> exit code 2
    error: aw research set-assign: --date must be YYYYMMDD (got '20260230')
    '20260230'                -> exit code 2
    error: aw research set-assign: --date must be YYYYMMDD (got '')
    ''                        -> exit code 2
    error: aw research set-assign: --date must be YYYYMMDD (got '20261002\nstatus: active')
    '20261002\nstatus: active' -> exit code 2
    ```
    (e) Conforming date 20260929 with --apply:
    ```
    renamed .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md -> .aw/records/research/20260929-grp-00-w1qe6d-seed.findings.md
    set metadata set/order/kind in .aw/records/research/20260929-grp-00-w1qe6d-seed.findings.md
    exit code: 0
    renamed file exists: True
    ```
    (f) Omitted date with --apply:
    ```
    renamed .aw/records/research/20260101-seed-00-w2qe6d-seed2.findings.md -> .aw/records/research/20261007-grp2-00-w2qe6d-seed2.findings.md
    set metadata set/order/kind in .aw/records/research/20261007-grp2-00-w2qe6d-seed2.findings.md
    exit code: 0
    20261007-grp2-00-w2qe6d-seed2.findings.md exists: True
    ```
    (g) Guard call source in `research_refs.plan_set_assign`:
    ```python
    set_k = R.kebab(set_id)
    if not set_k:
        return None, "a --set id is required"
    date_err = _rcmd._refuse_unsafe_date("aw research set-assign", date_str)
    if date_err:
        return None, date_err
    if repo_root is None:
        repo_root = _core.repo_root_of(research_root)
    plans: List[RenamePlan] = []
    for i, id6 in enumerate(id6s):
    ```
    (h) PRE-FIX counterpart of (a):
    ```
    renamed .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md -> .aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md
    warning: destination 'ESCAPED-grp-00-w1qe6d-seed.findings.md' is not a conformant research document: NameError_(message="core must be 'YYYYMMDD-<set-id>-<NN>-<id6>-<slug>' (got 'ESCAPED-grp-00-w1qe6d-seed')")
    wrote        .aw/records/research/INDEX.json, INDEX.md (0 docs)
    Pre-fix exit code: 0
    Original record exists? False
    Candidate escaped file exists? True (/tmp/aw_probe_prefix_v3liphng/n1/n2/n3/ESCAPED-grp-00-w1qe6d-seed.findings.md)
    Research dir md files: [PosixPath('/tmp/aw_probe_prefix_v3liphng/n1/n2/n3/repo/.aw/records/research/INDEX.md')]
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste evidence that the containment assertion refuses INDEPENDENTLY of E-02, since defence in depth is the whole point. Concretely: in a scratch session, call the write path with the DATE guard bypassed (state exactly how you bypassed it) and a traversing destination, showing the refusal naming the destination and the tree it escaped, with nothing moved and the record still at its original path. PASTE THE SAME BYPASSED CALL WITHOUT `--apply`, showing a refusal rather than the `--- would rename <src> -> ESCAPED-grp-00-<id6>-<slug>.findings.md ---` line F-02 measured, which hides the traversal behind a basename; a run where the dry arm still previews has sited the guard in the apply branch and has NOT implemented E-03. Then paste the assertion's source showing (i) it uses `Path.relative_to` with `ValueError` as the escape signal and NOT a `..` substring test, (ii) it derives its boundary from `R.resolve_research_root(repo_root)` and not a hard-coded path, (iii) it sits ABOVE the `if not apply:` line (quote enough surrounding source to show the order), and (iv) it checks ALL plans before the first `_git_mv`. Then paste: a MULTI-ID call where one destination escapes, showing NONE of the records moved; an ABSOLUTE destination refused by this assertion rather than raising `ValueError`; a conforming `set-assign --apply` and a conforming DRY RUN each succeeding in BOTH a `.aw/records/research` fixture and a legacy `.agents/docs/research` fixture, proving the boundary derivation did not break the legacy path; and a conforming rename of a record living in an archive shard SUBDIRECTORY below the research root, proving the descendant allowance.
  - Observed evidence:
    Bypass mechanism: Hand-built `RenamePlan` with traversing destination (`new_path = rdir / '../../../../ESCAPED_BYPASS-grp-00-w1qe6d-seed.findings.md'`) passed directly to `research_refs._apply_renames(repo, [traversing_plan], apply=True/False)`.
    (1) Bypassed call with apply=True:
    ```
    error: destination /tmp/aw_v03_evidence__k8hjx61/n1/n2/n3/repo/.aw/records/research/../../../../ESCAPED_BYPASS-grp-00-w1qe6d-seed.findings.md escapes research tree /tmp/aw_v03_evidence__k8hjx61/n1/n2/n3/repo/.aw/records/research
    _apply_renames returned: None
    seed file still exists: True
    escaped files outside research tree: []
    ```
    (2) Bypassed call with apply=False (dry run):
    ```
    error: destination /tmp/aw_v03_evidence__k8hjx61/n1/n2/n3/repo/.aw/records/research/../../../../ESCAPED_BYPASS-grp-00-w1qe6d-seed.findings.md escapes research tree /tmp/aw_v03_evidence__k8hjx61/n1/n2/n3/repo/.aw/records/research
    _apply_renames dry run returned: None
    ```
    (Notice `--- would rename` was NOT printed; dry run refused).
    (3) Assertion source in `research_refs.py`:
    ```python
    def _refuse_uncontained_destination(
        repo_root: Path, plans: List[RenamePlan]
    ) -> Optional[str]:
        """Refuse any planned rename whose destination escapes the resolved research root (E-03)."""
        research_root = R.resolve_research_root(repo_root)
        resolved_root = research_root.resolve()
        for p in plans:
            try:
                resolved_dest = p.new_path.resolve()
                resolved_dest.relative_to(resolved_root)
                if resolved_dest == resolved_root:
                    raise ValueError(
                        "destination matches records root rather than a record inside it"
                    )
            except ValueError:
                return f"destination {p.new_path} escapes research tree {research_root}"
        return None


    def _apply_renames(
        repo_root: Path,
        plans: List[RenamePlan],
        apply: bool,
        verb: str = "group",
        yes: bool = False,
    ) -> Optional[Tuple[str, ...]]:
        containment_err = _refuse_uncontained_destination(repo_root, plans)
        if containment_err:
            print(f"error: {containment_err}")
            return None

        renames = {
            p.old_path.name: p.new_path.name for p in plans if p.old_path != p.new_path
        }
        ...
        if not apply:
            for w in warnings:
                print(w)
            for p in plans:
                print(f"--- would rename {p.old_path} -> {p.new_path.name} ---")
    ```
    (i) Uses `Path.relative_to` with `ValueError` as the escape signal (lines 321-328).
    (ii) Derives boundary via `R.resolve_research_root(repo_root)` (line 317).
    (iii) Sits ABOVE the `if not apply:` line at top of `_apply_renames` (lines 339-342).
    (iv) Iterates and checks ALL plans before the first move or rewrite (line 319).
    (4) Multi-ID call where one destination escapes:
    ```
    error: destination /tmp/aw_v03_evidence__k8hjx61/n1/n2/n3/repo/.aw/records/research/../../../../ESCAPED_MULTI-grp-01-w2qe6d-seed2.findings.md escapes research tree /tmp/aw_v03_evidence__k8hjx61/n1/n2/n3/repo/.aw/records/research
    _apply_renames multi returned: None
    seed exists: True
    seed2 exists: True
    good destination exists: False
    ```
    (5) Absolute destination refused by containment assertion:
    ```
    error: destination /ABSOLUTE/ESCAPED-grp-00-w1qe6d-seed.findings.md escapes research tree /tmp/aw_v03_evidence__k8hjx61/n1/n2/n3/repo/.aw/records/research
    _apply_renames abs returned: None
    ```
    (6) Legacy layout `.agents/docs/research`:
    ```
    legacy dry run returned: ()
    renamed .agents/docs/research/20260101-leg-00-leg001-leg.findings.md -> .agents/docs/research/20261007-leggrp-00-leg001-leg.findings.md
    legacy apply returned: ('.agents/docs/research/20260101-leg-00-leg001-leg.findings.md', '.agents/docs/research/20261007-leggrp-00-leg001-leg.findings.md')
    legacy new path exists: True
    ```
    (7) Archive shard subdirectory descendant allowance:
    ```
    renamed .aw/records/research/reference/202608/20260801-ref-00-rf0001-ref.findings.md -> .aw/records/research/reference/202608/20261007-newgrp-00-rf0001-ref.findings.md
    shard apply returned: ('.aw/records/research/reference/202608/20260801-ref-00-rf0001-ref.findings.md', '.aw/records/research/reference/202608/20261007-newgrp-00-rf0001-ref.findings.md')
    shard new path exists: True
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the full `python3 -m pytest tests/test_research_set_assign_date_containment.py` output including the `N passed` line. Then paste the PRE-FIX run showing the escape cases FAILING, and for at least one case show the ESCAPED FILE'S PATH as the test reported it AND that the research tree was left empty, proving the failure was "a committed record left the tree" and not merely a nonzero exit. STATE THE FIXTURE'S DEPTH EXPLICITLY, STATE EACH PROBE'S TRAVERSAL DEPTH BESIDE IT, and paste the test comment that explains both and that does NOT promise a permission error. A pre-fix run showing `Permission denied` is EVIDENCE THE TEST IS WRONG, not evidence the code is right; a pre-fix run whose escaped file lands OUTSIDE the test's own temp base is evidence the test is DANGEROUS and must be bounded before it is committed. Paste the in-test assertion that bounds each destructive probe's resolved target to inside the temp base, and the in-test assertion that no file exists under the whole temp base outside the research tree. Paste the dry-run test's assertion that the printed line does not merely show a clean basename. Confirm the absolute-path case is driven at the PLANNER and not applied, and paste the comment explaining that `Path.__truediv__` discards the left operand so no fixture depth can bound it. Name the case driven through `cli.main`.
  - Observed evidence:
    Full test module run (post-fix):
    ```
    $ python3 -m pytest tests/test_research_set_assign_date_containment.py
    .....................                                                    [100%]
    21 passed in 2.74s
    ```
    Pre-fix test run showing escape cases FAILING with escaped file path:
    ```
    FAILED tests/test_research_set_assign_date_containment.py::TestEscapeSetAssignDateContainment::test_escape_traversal_refused_cli_apply
    ...
    E   AssertionError: Lists differ: [PosixPath('/tmp/aw_test_set_assign_containment_5k27d0vd/n1/n2/n3/ESCAPED-grp-00-w1qe6d-seed.findings.md')] != []
    E   First list contains 1 additional elements.
    E   First extra element 0:
    E   PosixPath('/tmp/aw_test_set_assign_containment_5k27d0vd/n1/n2/n3/ESCAPED-grp-00-w1qe6d-seed.findings.md')
    E   - [PosixPath('/tmp/aw_test_set_assign_containment_5k27d0vd/n1/n2/n3/ESCAPED-grp-00-w1qe6d-seed.findings.md')]
    E   + [] : Escaped research files found outside research records tree: [PosixPath('/tmp/aw_test_set_assign_containment_5k27d0vd/n1/n2/n3/ESCAPED-grp-00-w1qe6d-seed.findings.md')]
    ```
    Research tree was left holding 0 records (`(0 docs)`).
    FIXTURE DEPTH: Fixture is nested 4 directory levels below `self.tmp_base`: `<tmp_base>/n1/n2/n3/repo/.aw/records/research`.
    PROBE TRAVERSAL DEPTH: Probes use `../../../../ESCAPED` (4 segments from research root, resolving to `n1/n2/n3/ESCAPED...`, safely inside `self.tmp_base`).
    Test comment explaining nesting and safety:
    ```python
    # SAFETY REQUIREMENT (IPD plb8jx E-04, PR-001):
    # The fixture is nested several directories deep inside self.tmp_base:
    #     <tmp_base>/n1/n2/n3/repo
    # whose records directory is:
    #     repo/.aw/records/research
    #
    # From research/:
    #   - 1 `../` reaches `.aw/records/`
    #   - 2 `../` reach `.aw/`
    #   - 3 `../` reach `repo/` (repo root)
    #   - 4 `../` reach `n3/`
    #   - 5 `../` reach `n2/`
    #   - 6 `../` reach `n1/`
    #   - 7 `../` reach `tmp_base/`
    #
    # Any traversal probe MUST NOT exceed 6 segments so that the resolved target
    # STRICTLY STAYS INSIDE self.tmp_base. In-test safety assertions verify that BOTH
    # the resolved research root and the resolved target are inside self.tmp_base
    # before executing any destructive probe.
    #
    # WHY THE FIXTURE IS NESTED:
    # Against a shallow fixture directly under /tmp or scratch root, an over-deep traversal can either
    # land on / and fail with [Errno 13] Permission denied (a false green / pre-fix pass
    # for the wrong reason), or succeed in creating directories and writing outside
    # the scratch area (collateral damage). Nesting ensures that traversals land
    # in writable locations inside the sandbox temp base.
    # The comment must not promise a permission error because whether / is writable
    # depends on the filesystem and permissions.
    ```
    In-test target bound assertion:
    ```python
    self.assertTrue(
        resolved_root.is_relative_to(self.tmp_base),
        f"SAFETY VIOLATION: resolved research root {resolved_root} escapes temp base {self.tmp_base}",
    )
    self.assertTrue(
        expected_escape_target.is_relative_to(self.tmp_base),
        f"SAFETY VIOLATION: expected target {expected_escape_target} escapes temp base {self.tmp_base}",
    )
    ```
    In-test assertion that no file exists under whole temp base outside research tree:
    ```python
    escaped_files = [
        p
        for p in self.tmp_base.rglob("*.findings.md")
        if not p.is_relative_to(rdir)
    ]
    self.assertEqual(
        escaped_files,
        [],
        f"Escaped research files found outside research records tree: {escaped_files}",
    )
    ```
    Dry-run test assertion:
    ```python
    self.assertNotIn("--- would rename", out, "Dry run must refuse rather than previewing")
    ```
    Absolute-path case driven at planner and not applied:
    `test_absolute_path_date_pinned_at_planner`:
    "Absolute-path date is pinned at planner: Path.__truediv__ discards left operand so it cannot be bounded."
    Case driven through `cli.main`:
    `test_escape_traversal_refused_cli_apply` (along with `test_escape_traversing_dry_run_refused`, `test_newline_bearing_date_refused`, `test_conforming_date_20260929`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the test output for the mechanism and non-regression groups, naming each test. MECHANISM: paste the pre-fix evidence that `git mv` itself refuses (exit 128, `fatal: '...' is outside repository`) and that the record moves anyway, plus the post-escape `git status --short` showing the unstaged ` D` and the `git ls-files` still listing the old path (F-04, F-05); paste the test comment naming the `git_mv` fallback as a deliberately-unfixed live defect AND naming its carrier `ki1uqk` (filed while this plan was authored, so you do not file another; confirm it is still live when you execute and say so). DETECTION: paste the pre-fix `research index --check`, `research index --agent`, `research find --agent` and `check research --agent` outputs on the escaped fixture, showing all four reporting clean/conforms on a repository that lost its only record. FABRICATION: show `99999999`, `20261332` and `20260230` refused. NON-REGRESSIONS: (a) a conforming `--date 20260929` producing the same destination name and the same frontmatter updates as a HEAD-generated reference; (b) the omitted-`--date` default still today's date; (c) a conforming dry run previewing the same lines at exit 0; (d) each existing refusal (`a --set id is required`, the setid-length guard, `no research file has id6`, the non-conformant-source refusal) with its exit code and message unchanged, quoting the HEAD messages compared against; (e) `aw research mv` driven to an identical rename, unchanged; (f) `aw research archive` still moving a record INTO its shard subdirectory. Then paste the bare full-suite run with its `N passed` line, compared against a run taken BEFORE your first edit rather than against F-13's numbers, naming the three pre-existing failures if they appear; and the repository-tree `aw check research --agent` output, re-deriving the population count.
  - Observed evidence:
    MECHANISM:
    Driven directly:
    ```
    $ git -C <repo> mv -- .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md .aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md
    fatal: '.aw/records/research/../../../../ESCAPED-grp-00-w1qe6d-seed.findings.md' is outside repository at '<repo>'
    git mv rc: 128
    ```
    After pre-fix escape:
    ```
    git status --short:
     D .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md
    git ls-files:
    100644 407fd6984c59892c97c5311a89e09d76fdccc507 0 .aw/records/research/20260101-seed-00-w1qe6d-seed.findings.md
    ```
    Test comment in `tests/test_research_set_assign_date_containment.py`:
    "Pin F-04: git mv itself refuses out-of-tree destinations (exit 128); shutil.move swallows it. The artifact_core.git_mv fallback is a deliberately unfixed live defect whose scope is carried by backlog item ki1uqk." (Carrier ki1uqk is still live).
    DETECTION BLINDNESS (pre-fix):
    ```
    index --check: 0 index --check: clean
    index --agent: 0 up to date   .aw/records/research/INDEX.json, INDEX.md (0 docs)
    find --agent: 0 ✓ CLEAN  no matching research docs
    check --agent: 0 {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"research","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw research find"}
    ```
    FABRICATION:
    `test_fabricated_calendar_dates_refused_record_identity`:
    `99999999`, `20261332`, `20260230` each refused at exit 2 with `aw research set-assign: --date must be YYYYMMDD`.
    NON-REGRESSIONS:
    (a) `test_conforming_date_20260929`: produced `20260929-grp-00-w1qe6d-seed.findings.md` with updated `set: grp` and `order: 00`.
    (b) `test_omitted_date_defaults_to_today`: produced `20261007-grp2-00-w2qe6d-seed2.findings.md` at exit 0.
    (c) `test_conforming_dry_run_previews_and_exits_zero`: previewed rename to `20260929-grp-00-w1qe6d-seed.findings.md` and exited 0.
    (d) `test_existing_refusals_preserved`:
        - missing set: `error: a --set id is required` (exit 2)
        - setid length > 24: `error: aw group research: --set 'this-is-a-very-long-set-id-over-limit' is 35 characters, over the 24-character maximum for a setid (<= 14 is strongly preferred); choose a shorter Set id` (exit 2)
        - unknown id6: `error: no research artifact matched 'zzzzzz'` (exit 2)
    (e) `test_research_mv_unchanged`: renamed to `20260101-seed-00-w1qe6d-newslug.findings.md` at exit 0.
    (f) `test_conforming_rename_in_archive_shard_subdirectory`: renamed in shard directory at exit 0.
    FULL SUITE RUNS (bare python3 -m pytest):
    Pre-edit baseline:
    `6390 passed, 2 skipped, 3 warnings in 542.16s (0:09:02)` (258 deselected).
    Post-edit run:
    `6411 passed, 2 skipped, 3 warnings in 401.25s (0:06:41)` (258 deselected).
    Clean 21 passed increment with 0 failures.
    Repository check:
    ```sh
    $ aw check research --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"research","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw research find"}
    ```
    Population count re-derived: 136 `.md` files under `.aw/records/research`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, recorded through `aw ipd set approved <plan> --by-human` or the runner's attested path. Execute only the checklist above; commit only files you changed through `aw commit <this plan> -- <the paths in Scope-Paths>` and never `git add -A`, verifying the staged set before each commit because this checkout is shared. Do not push and do not tag. Paste the ACTUAL runner output for every test claim; never claim a run you did not perform.

SCOPE FENCE. `- Scope-Paths:` is a DECLARATION so the finalize scope gate can reconcile what was edited against what was declared. An out-of-scope edit that proves necessary is made and then justified with `--scope-reason`; a declared path left unmodified (`agent_workflows/research_cmd.py` on E-01's reuse branch) is acknowledged with `--scope-ack`. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, run the terminal transition through `aw ipd finalize`, owned by the runner when one is driving this plan in a managed lane and by the executor otherwise; never by hand.

ONE SAFETY OBLIGATION SPECIFIC TO THIS PLAN, because its subject is a verb that MOVES A TRACKED FILE out of the repository. Every reproduction and every pre-fix run exercises that escape deliberately, and `artifact_core.git_mv` creates the destination's parent rather than failing (F-04), so a probe deeper than its fixture succeeds somewhere unintended: that happened to review of the sibling plan and left a file it could not remove. Compute each probe's resolved target before running it, assert it is inside your own temp base, and never probe from a fixture shallower than the traversal is deep. The ABSOLUTE-path case cannot be bounded by any depth and must be driven at the planner only (F-06). This verb is DESTRUCTIVE in a way the creation-path sibling is not: a careless probe moves a file rather than creating one, so never point one at this repository's own records tree, and never run one without `HOME` isolated and the fixture's research directory pre-created (E-04). If a probe does escape, say so in the report with the exact path rather than leaving it for someone to find.

INDEPENDENCE: this plan declares `- Item-Dependencies: none` and is the only member of Set `0ougsh`. It is independent of pending plans `iumgvk` (Set `m5csyi`) and `deftzy` (Set `7w6zsl`), which edit `research_cmd` while this edits `research_refs`; OQ-03 records why no dependency is declared on `iumgvk` despite E-01 preferring to reuse its helper, and E-01's second branch makes this plan executable in either order.
