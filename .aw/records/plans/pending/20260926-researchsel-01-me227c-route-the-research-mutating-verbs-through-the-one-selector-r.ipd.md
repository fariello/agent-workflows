# IPD: Route the research mutating verbs through the one selector resolver

- Date: 2026-09-26
- Kind: child
- Concern: THE RESEARCH MUTATING VERBS BYPASS THE ONE SELECTOR RESOLVER, so the same selector resolves differently per verb. `selectors`'s module docstring states "every verb (`rename`, `group`, `set`/..., `show`, `find`, `archive`, and the per-area set-assign/mv paths) routes selector resolution through `resolve()` here, so the SAME selector resolves to the SAME file for every verb". For research that is false: `research_archive.run_archive` (targeted branch: `if parsed.id6 == target or parsed.set_id == target`), `research_archive.plan_transition` (`if parsed.id6 == id6`), `research_refs._find_by_id6` (used by `plan_set_assign` and `plan_mv`, i.e. `aw group research` and `aw rename research`), and `research_cmd.plan_set_outcome` / `research_cmd.plan_set_priority` each match against the PARSED FILENAME with a private loop, and none of the three modules imports `selectors`. Re-measured at HEAD `61ef21d8`: `aw find research reference` lists 66 documents; `aw archive research reference` prints `no research doc or set matches 'reference'` (exit 0); `aw rename research reference` prints `error: no research file has id6 'reference'`. `selectors.resolve_for_mutation(repo, "research", "reference")` meanwhile returns the ruled refusal `selector 'reference' is ambiguous (status) matching multiple files; pass --force to act on all`, and for setid `awmetastore` returns 7 paths, the same 7 `aw archive research awmetastore` previews today. TWO HAZARDS FOUND AT REVIEW THAT THE ROUTING MUST CARRY, both measured (review PR-601/PR-602), because "route through the resolver" is NOT behavior-preserving as stated: (1) THE TWO AUTHORITIES DISAGREE ABOUT WHERE RESEARCH LIVES. `selectors.record_dirs` resolves `research` via `record_producers.resolve_record_read_paths` plus the literal `.aw/records/research` and `.agents/research`; it does NOT know the legacy `.agents/docs/research` that `research_contract.resolve_research_root` returns and that `research_contract.RESEARCH_ROOT` names. On a repo using the legacy layout with no retention manifest, `resolve_for_mutation(root, "research", "<any id6>")` returns `no research artifact matched`, so the routing turns a WORKING archive/rename into a silent no-match. This is not hypothetical: it is the layout EVERY existing research test fixture builds (`tests/test_research_archive.py`, `tests/test_research_cmd_create.py`, `tests/test_research_index.py` all use `root / R.RESEARCH_ROOT`), so the shipped `TargetedArchiveTests` would fail. (2) THE RESOLVER'S `path` KIND IS NOT CONFINED TO THE RESEARCH TREE. `resolve(repo, "research", "README.md")` matches by `MATCH_PATH` and returns the repo's OWN `README.md`, because the path rule tests `is_file()` and never that the hit is a research record. Driven at review: fed to `plan_set_outcome` that path plans a 26200-byte rewrite of `README.md` (635622 bytes for `agent_workflows/cli.py`), and `plan_mv`/`plan_set_assign` raise `AttributeError` on `R.parse_name(...).kind` because the name does not parse. `selectors.resolve_one` already denies `MATCH_PATH` for exactly this class of reason, and `aw find` denies it too (`cli._resolve_selectors_with_kinds`).
- Scope: IN: (a) `selectors.record_dirs` learns the LEGACY research read path `.agents/docs/research`, which it does not know today and which `research_contract.resolve_research_root` does (review PR-601: without this the routing is a REGRESSION, not a fix, on every legacy-layout repo AND on the whole existing test fixture population); (b) a shared `_resolve_one_research` / `_resolve_research_for_mutation` helper that DENIES `selectors.MATCH_PATH` and CONFINES every resolved path under the research root (review PR-602: the resolver's `path` kind otherwise accepts any repo file, and the research planners then corrupt or crash on it); (c) `research_archive.run_archive`'s targeted branch resolves `target` through that helper and feeds each resolved path into a path-keyed transition planner; (d) `research_archive.plan_transition` gains a path-keyed core (`plan_transition_for_path`) that the id6 entry point and the resolver path both use, so the per-doc rules (research-prompt hot-status refusal, shard target) live once; (e) `research_refs._find_by_id6` resolves through the helper with UNIQUE semantics (exactly one file, or the refusal), which routes `aw rename research` and `aw group research`; (f) `research_cmd.plan_set_outcome` and `plan_set_priority` resolve their single target the same way; (g) a `--force` flag on `aw archive` (declared on `p_archive` in `cli._build_parser` and in the `archive` `CommandDeclaration.legacy_flags` in `command_surface`), threaded to the resolver; (h) behavioral parity and refusal tests, including the legacy-layout and out-of-tree-path cases. OUT: the bare age sweep (`sweep_candidates`), which selects by age not selector; `plans_archive`; the resolver's own AMBIGUITY policy (`resolve_for_mutation`'s kind rules are consumed, never edited); porting research readers to `artifact_meta` (spec `4sd62s`).
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/research_archive.py, agent_workflows/research_refs.py, agent_workflows/research_cmd.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_research_archive.py, tests/test_cli_find.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: mblu3p
- Blocks-Release: next
- Set: researchsel
- Order: 1
- Highest E allocated: 12
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: me227c

## Workflow history
- 2026-09-26 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-601..PR-607 all FIXED (two BLOCKERs found by measurement: legacy-layout regression and unconfined path selector). 8 items -> 12 with a 12:12 E/V bijection.

- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-607 all FIXED. Two BLOCKERS found by MEASUREMENT, not by reading: routing through `selectors.resolve_for_mutation` is a silent REGRESSION on the legacy `.agents/docs/research` layout (which every existing research test fixture builds), and the resolver's `path` kind is unconfined, so `aw research set-outcome README.md` would plan a rewrite of the repository README. Added E-02 (reproduce both), E-03 (teach `record_dirs` the legacy path), E-04 (one confined research resolver denying `MATCH_PATH`) and E-10 (guard tests, each shown failing with its own guard reverted); renumbered the rest to 12 items with a 12:12 E/V bijection. `selectors.py` and `tests/test_cli_find.py` added to `- Scope-Paths:`. OQ-03 and OQ-04 recorded as resolved. Structural lint conforming at `--phase author` before and `--phase review-finalize` after. Review record: `.aw/records/reviews/20260926-researchsel-01-me227c-route-the-research-mutating-verbs-through-the-one-selector-r.review.md`.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog mblu3p. All three symptoms and the resolver's ruled outcomes re-measured at HEAD 61ef21d8; the item's research_cmd line offsets were re-identified by symbol (plan_set_outcome/plan_set_priority), and aw archive was found to have no --force flag.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every research verb that mutates by selector (`archive`, `rename`, `group`, `set-outcome`, `set-priority`) resolve that selector through `selectors.resolve_for_mutation`, so a selector learned from `aw find research` either acts on the same documents or refuses with the resolver's explanation, never a silent no-match.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE at the executing HEAD, on the real tree, READ-ONLY (previews only, never `--apply`): paste `aw find research reference | grep -c '^✓'`, `aw archive research reference`, `aw rename research reference`, `aw archive research awmetastore | grep -c 'would archive'`, and for tokens `reference`, `awmetastore`, and one real id6 (e.g. `i5gj61`) the `(kind, len(paths))` of `selectors.resolve(Path('.'), 'research', tok)` and the `(len(paths), error)` of `selectors.resolve_for_mutation`. Also paste `rg -n "^from|^import" agent_workflows/research_archive.py agent_workflows/research_refs.py agent_workflows/research_cmd.py | rg selectors` (expected empty).
  - Depends on: none
  - Expected outcome: find 66 (or the current count), archive and rename report no match; `awmetastore` previews 7 and the resolver returns the same 7; `reference` is `status` kind and `resolve_for_mutation` refuses with the `--force` message.
  - Execution state: pending

- [ ] E-02 REPRODUCE THE TWO REVIEW HAZARDS before changing anything, on THROWAWAY temp repos, so the two guards below are driven by measurement rather than by this plan's prose. (a) LEGACY LAYOUT: build a temp git repo with one conformant doc under `root / R.RESEARCH_ROOT` (the value `research_contract.RESEARCH_ROOT` holds, which is what every existing research test fixture uses), then paste `R.resolve_research_root(root)`, `selectors.record_dirs(root, "research")`, and `selectors.resolve_for_mutation(root, "research", "<that id6>")`. (b) UNCONFINED PATH: on the REAL tree, paste `selectors.resolve(Path('.'), 'research', 'README.md')` showing `kind='path'` and the repo's own `README.md`, and `R.parse_name('README.md')` returning `(None, <error>)`.
  - Depends on: E-01
  - Expected outcome: (a) `resolve_research_root` returns `.agents/docs/research` while `record_dirs` returns `[]`, so `resolve_for_mutation` answers `no research artifact matched` for a document that plainly exists - the measured proof that routing without E-03 is a regression; (b) the resolver returns a NON-research file for a `path` token, and `parse_name` cannot parse it, the measured proof that E-04's confinement is required.
  - Execution state: pending

### Task group 2: make the resolver usable for research

- [ ] E-03 TEACH `selectors.record_dirs` THE LEGACY RESEARCH READ PATH. In `selectors._record_dirs_cached`, beside the existing literal `_add(repo_root / ".aw" / "records" / record_type)` / `_add(repo_root / ".agents" / record_type)` pair, add the research-specific legacy nesting `_add(repo_root / ".agents" / "docs" / "research")` when `record_type == "research"`, citing `record_producers._LEGACY_RECORD_CLASS_SUBPATHS["research"] == "docs/research"` as the authority for the subpath and `research_contract.resolve_research_root` as the authority that research reads it. `_add` already no-ops a non-existent dir and de-duplicates by resolved path, so this ADDS a directory and removes none. Verify NO PERTURBATION of this repo by pasting `selectors.record_dirs(Path('.'), 'research')` before and after (must be byte-identical: this repo has no `.agents/`), and confirm the legacy fixture from E-02(a) now resolves.
  - Depends on: E-02
  - Expected outcome: this repo's `record_dirs` unchanged; the E-02(a) fixture's `resolve_for_mutation` now returns that one document instead of `no research artifact matched`; `aw find research <id6>` keeps its current answer on the real tree.
  - Execution state: pending

- [ ] E-04 ADD THE ONE CONFINED RESEARCH RESOLVER that every research verb below calls, so the confinement cannot be implemented three times and drift. Add `_resolve_research_for_mutation(repo_root, research_root, selector, *, force=False) -> (paths, error)` (place it where all three modules can import it without a cycle - `research_archive` is the natural home since `research_refs` and `research_cmd` may both import it; paste `python3 -c "import agent_workflows.research_cmd, agent_workflows.research_refs, agent_workflows.research_archive"` succeeding). It MUST: (1) call `selectors.resolve_for_mutation(repo_root, "research", selector, force=force, deny=frozenset({selectors.MATCH_PATH}))`, matching what `selectors.resolve_one` and `cli._resolve_selectors_with_kinds` already deny and letting the resolver render the `rejected_kind` message rather than a silent no-match; and (2) DROP any resolved path not under `research_root` and any whose `R.parse_name(p.name)` does not parse, returning a refusal naming the selector when that empties the set - a defense in depth that holds even if the precedence or the deny set changes later. Also add `_resolve_one_research(...)` returning exactly one path or an error, for the rename/group/set-outcome callers.
  - Depends on: E-03
  - Expected outcome: an id6 and a setid resolve exactly as `aw find research` resolves them; `README.md` and `agent_workflows/cli.py` are REFUSED with an empty path set rather than returned; a path to a real research document is ALSO refused, which is PARITY with `aw find research <path>` (it matches nothing there either, because `cli._resolve_selectors_with_kinds` denies the kind) and is the deliberate answer to OQ-04.
  - Execution state: pending

### Task group 3: one per-doc planner

- [ ] E-05 FACTOR `research_archive.plan_transition` into a path-keyed core. Add `plan_transition_for_path(research_root, path, new_status)` that reads the doc's parsed name and front matter (the same `R.parse_name` + `R.parse_frontmatter` `_all_docs` uses), applies the existing checks (status in `R.STATUSES`; research-prompt carries no hot status) and returns the `Move`; make `plan_transition(research_root, id6, new_status)` locate the path and delegate. Keep `plan_transition`'s signature and messages so its callers (the sweep branch of `run_archive`, `research_cmd`, tests) are unchanged; list every caller with `rg -n "plan_transition\(" agent_workflows tests` and paste it.
  - Depends on: E-01
  - Expected outcome: existing `TransitionTests`, `TargetedArchiveTests`, `SweepTests`, `PromptArchiveTests` pass unchanged; a path that is not a conformant research doc returns an error rather than a `Move`.
  - Execution state: pending

### Task group 4: route through the resolver

- [ ] E-06 ROUTE `run_archive`'s TARGETED branch through `_resolve_research_for_mutation(repo_root, research_root, target, force=bool(getattr(args, "force", False)))` (E-04's helper, NOT `selectors.resolve_for_mutation` directly - the confinement and the `MATCH_PATH` deny must not be bypassed). On an error, print it as `error: <msg>` and return 2 (a refusal is not the empty result). On success, build one `Move` per resolved path via `plan_transition_for_path(..., "archive")`, skipping (and counting in the preview) a path already in the archive shelf so re-archiving is idempotent, then keep the existing preview/apply/commit-offer flow. The helper's `no ... artifact matched` case keeps using the existing `Term().empty_result` rendering (exit 0) so a genuine no-match reads as today; distinguish it from a REFUSAL by testing for that exact prefix rather than by truthiness of the error.
  - Depends on: E-04, E-05
  - Expected outcome: id6 and setid targets preview exactly the documents they preview today, INCLUDING on a legacy-layout repo; a `status` or filename-substring multi-match without `--force` exits 2 with the resolver's ambiguity message; with `--force` it previews every match.
  - Execution state: pending

- [ ] E-07 ADD `--force` TO `aw archive`: register it on `p_archive` in `cli._build_parser` with help mirroring the rename/group `--force` ("act on ALL matches when a status or filename-substring selector is ambiguous; does not override a unique-id collision; a setid needs no force"), and add `"--force"` to the `archive` `CommandDeclaration.legacy_flags` in `command_surface`. `cli._run_archive` already copies `vars(args)` into the backend namespace, so no dispatch change is needed; confirm by reading it and paste the lines. Plans archive ignores the flag (it does not read it); state that in the help text. NOTE what the surface tests do and do not prove: `tests/test_command_surface_declarations.py` asserts only that no parser LEAF is undeclared (`find_undeclared_leaves`), and NO shipped test compares `archive`'s `legacy_flags` against its parser, so a green suite does NOT confirm the declaration was updated - V-07 therefore asserts the tuple contents directly.
  - Depends on: E-06
  - Expected outcome: `aw archive --help` lists `--force`; `cs.get_declaration("archive").legacy_flags` contains `--force`; `python3 -m pytest tests/test_command_surface_declarations.py tests/test_workflow_artifacts_prune.py -o addopts="" -q` passes.
  - Execution state: pending

- [ ] E-08 ROUTE `research_refs._find_by_id6` through `_resolve_one_research` with UNIQUE semantics: return the single path when exactly one resolves, and otherwise return an error string the two planners print (the resolver's own message, or `selector <tok> matched N research files; rename/group target one document per token` for a multi-path setid). The helper needs `repo_root`, which `_find_by_id6` does not have: thread it from `run_set_assign`/`run_mv`, which already hold it via `_repo_root(args)`, rather than trying to invert `research_root` (there is no such inverse, and `resolve_research_root` is one-way). Change `plan_set_assign`/`plan_mv` to propagate that message instead of the fixed `no research file has id6` text. GUARD THE CRASH the confinement now prevents: after resolving, `plan_mv`/`plan_set_assign` still call `R.parse_name(src.name)` and use `.kind`/`.slug`/`.order`, so a non-parsing name must be refused BEFORE that (measured at review: it raised `AttributeError: 'NoneType' object has no attribute 'kind'`).
  - Depends on: E-04
  - Expected outcome: `aw rename research <id6>` behaves as today; `aw rename research reference` refuses with the resolver's status-ambiguity message instead of `no research file has id6`; a path token (to a research doc or not) refuses per OQ-04 rather than raising `AttributeError`.
  - Execution state: pending

- [ ] E-09 ROUTE `research_cmd.plan_set_outcome` and `plan_set_priority` target lookup through the same `_resolve_one_research` helper. These two take `research_root` and NOT `repo_root` (`research_cmd._research_root` discards it), and their five shipped test call sites pass a bare `research_root` positionally, so EITHER thread `repo_root` in as an optional parameter defaulting to a derivation, OR update those call sites; state which and why, and keep `tests/test_research_cmd_create.py::SetOutcomeTests` (5 call sites) passing. Also note `run_set_outcome`/`run_set_priority` then call `target.relative_to(root)`, which raises `ValueError` for any path outside the research root (measured at review), so E-04's confinement is what keeps those two functions safe.
  - Depends on: E-08
  - Expected outcome: `aw research set-outcome <id6>` behaves as today; a non-unique selector refuses with the resolver's message; `tests/test_research_cmd_create.py` passes.
  - Execution state: pending

### Task group 5: prove it

- [ ] E-10 ADD THE TWO GUARD TESTS for E-03 and E-04, which are the cases that make the routing safe rather than the cases that make it work. In `tests/test_research_archive.py`: (a) LEGACY LAYOUT PARITY - a temp repo whose docs live under `root / R.RESEARCH_ROOT` (what `_write_doc` already builds), asserting `selectors.record_dirs(root, "research")` includes that directory AND that a targeted `run_archive` by id6 and by setid still archives exactly the same documents it archives today; (b) CONFINEMENT - `_resolve_research_for_mutation(repo, rroot, "README.md")` (with a real `README.md` written at the repo root) returns an EMPTY path set with a refusal, and `research_refs.plan_mv` / `research_cmd.plan_set_outcome` given that token return an error rather than raising or planning a write to it. Add to `tests/test_cli_find.py` one case pinning that `record_dirs` for a NON-research type is unchanged by E-03, so the legacy nesting cannot leak to another type.
  - Depends on: E-03, E-04
  - Expected outcome: (a) passes both before and after E-06 ONLY once E-03 lands (it FAILS against E-03-less code, which is the point); (b) FAILS against a routing that omits E-04's confinement, proving the guard is load-bearing rather than decorative.
  - Execution state: pending

- [ ] E-11 ADD THE BEHAVIORAL PARITY AND REFUSAL TESTS to `tests/test_research_archive.py` on a temp git repo built with the existing `_write_doc` helper: two sets (`alpha` with 3 docs, `beta` with 2), mixed statuses (at least two docs `reference`, one `active`), all under `R.RESEARCH_ROOT`. (1) PARITY: for an id6 and for the setid `alpha`, the set of paths the CONFINED helper returns equals the set of `old_path`s `run_archive` previews (capture stdout, or call the planning step directly if E-06 exposes one); (2) STATUS REFUSAL: `run_archive(target="reference", apply=False)` returns 2 and prints `ambiguous (status)` and `--force`; with `force=True` it previews exactly the two `reference` docs; (3) NO-MATCH: an unknown token returns 0 with the empty-result text, unchanged; (4) APPLY via setid moves exactly the `alpha` docs into the archive shelf and nothing else; (5) RENAME: `research_refs.plan_mv` for `reference` refuses with the resolver's message; (6) SET-OUTCOME: `research_cmd.plan_set_outcome(rroot, "reference", ...)` refuses with the resolver's message; (7) PATH PARITY WITH `aw find` (OQ-04): a repo-relative path token to a REAL research document is REFUSED by every routed verb, matching what `aw find research <path>` does today. Update the call signatures in existing tests ONLY if E-08/E-09 changed a planner's parameters, and say which changed.
  - Depends on: E-06, E-07, E-08, E-09
  - Expected outcome: all pass; (2), (5) and (6) FAIL against the pre-change code; (1), (3), (4) and (7) pass before and after (they pin preserved behavior - (7) because a path token matches nothing today either, for a different internal reason).
  - Execution state: pending

- [ ] E-12 RUN THE BARE SUITE `python3 -m pytest` before and after and compare failing node IDs; then re-run E-01's commands (previews only).
  - Depends on: E-11
  - Expected outcome: the after-minus-before failing node set is empty; `aw archive research reference` now refuses with the ambiguity message (exit 2); `aw archive research awmetastore` still previews 7.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.resolve_for_mutation` is the ruled mutation policy (OQ-01 of IPD `laykok`, resolved by human): setid multi-match acts on all with no `--force`; a unique-kind (path/id6/stem) collision always refuses; a substring (and, as measured, status) multi-match refuses unless `--force`. `artifact_rename.run_rename` already applies it for the generic types.
- The rename/group parsers already carry a `--force` flag with that meaning (`cli._build_parser`, "IPD laykok E-07"); `aw archive` does not, so adding it is required for the policy's escape hatch to exist on archive.
- `command_surface.CommandDeclaration.legacy_flags` declares each command's accepted flags, and a new flag is declared there too - but be precise about what enforces it (review PR-605): the shipped `tests/test_command_surface_declarations.py` checks only `find_undeclared_leaves` (undeclared parser LEAVES), and no shipped test compares `archive`'s `legacy_flags` to its parser. Only `prompts new` has such a test (`tests/test_prompts_new.py::test_the_declared_flag_surface_matches_the_parser`). So the declaration update is a CONVENTION the suite does not verify for this command, which is why V-07 asserts the tuple contents directly instead of resting on a green run.
- `research_archive.plan_transition` is the one place per-doc archive rules live (research-prompt hot-status refusal, shard path); routing through the resolver must not fork those rules, hence E-05.
- THE TWO ROOT AUTHORITIES ARE NOT INTERCHANGEABLE, which is the fact this plan turns on (review PR-601). `research_contract.resolve_research_root(repo_root)` and `selectors.record_dirs(repo_root, "research")` are independent resolutions of "where research lives", and they DISAGREE on the legacy layout: the former knows `.agents/docs/research` (and `research_contract.RESEARCH_ROOT` is literally that string), the latter knows only what `record_producers.resolve_record_read_paths` yields plus the literal `.aw/records/research` / `.agents/research`. Routing a verb from the first authority to the second is therefore a BEHAVIOR CHANGE on the legacy layout, not a no-op, and E-03 closes the gap before any verb depends on it.
- THE RESOLVER'S `path` KIND IS UNCONFINED BY DESIGN and every caller confines it itself (review PR-602). `selectors._hits_for(MATCH_PATH)` returns any `is_file()` hit under the repo, with no check that it is a record of the requested type; `resolve_one` denies `MATCH_PATH` outright and `cli._resolve_selectors_with_kinds` (behind `aw find`) does the same. A research verb routing through `resolve_for_mutation` without a deny inherits that unconfined behavior, so the deny belongs in E-04's helper, NOT in `selectors`.
- Tests exercise behavior (maintainer ruling 2026-09-26: no source-text or structure pins, so no test asserts that a module imports `selectors`). Suites run BARE as `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `research_archive.run_archive` targeted branch | Filename-only id6/setid match; status/path/stem/substring selectors silently no-match. | `aw find research reference` -> 66 rows; `aw archive research reference` -> `no research doc or set matches 'reference'`. |
| F-2 | HIGH | `research_refs._find_by_id6` (rename/group) | Same bypass; message claims the token is an id6. | `aw rename research reference` -> `error: no research file has id6 'reference'`. |
| F-3 | MEDIUM | `research_cmd.plan_set_outcome`, `plan_set_priority` | Two further private loops matching `parsed.id6 == id6`; these are the functions behind the backlog item's `research_cmd.py:473`/`:598` offsets, re-identified by symbol. | `rg -n "parsed.id6 == " agent_workflows/research_cmd.py` -> two hits, in those functions. |
| F-4 | MEDIUM | `cli._build_parser` `p_archive` | `aw archive` has no `--force`, so the resolver's documented override for a status/substring multi-match would be unreachable. | `p_archive` arguments: `type_or_target`, `target`, `--age`, `--dir`, `--keep`, `--apply`, commit flags. |
| F-5 | INFO | resolver outcomes the fix will adopt | `resolve_for_mutation(".", "research", ...)`: `reference` -> refused (status ambiguity, `--force`); `awmetastore` -> 7 paths, equal to today's archive preview of 7; `i5gj61` -> 1 path. | Measured directly. |
| F-6 | INFO | backlog `mblu3p`'s honest scope note | Routing through the resolver changes what `aw archive research archive` does (32 docs match status `archive`); under the ruled policy it now REFUSES without `--force` rather than moving 32 documents, so the widening the item warns about requires an explicit `--force`. | `resolve_for_mutation(".", "research", "archive")` -> refused, 32 candidates. |
| F-7 | BLOCKER | `selectors.record_dirs` vs `research_contract.resolve_research_root` (review PR-601) | THE ROUTING IS A SILENT REGRESSION ON THE LEGACY LAYOUT until E-03 lands. The two root authorities disagree: `resolve_research_root` knows `.agents/docs/research`, `record_dirs` does not, so on a legacy-layout repo with no retention manifest the resolver answers `no research artifact matched` for a document that exists, and a WORKING `aw archive research <id6>` becomes a silent no-match at exit 0. It also breaks the shipped suite, because every research fixture builds that layout via `root / R.RESEARCH_ROOT`. | Temp repo, one doc under `.agents/docs/research`: `resolve_research_root` -> `.agents/docs/research`; `record_dirs` -> `[]`; `resolve_for_mutation(root,"research","bbbbbb")` -> `([], "no research artifact matched 'bbbbbb'")`, while today's `run_archive(target="bbbbbb", apply=True)` archives it (rc 0). Same layout used by `tests/test_research_archive.py`, `tests/test_research_cmd_create.py`, `tests/test_research_index.py`. |
| F-8 | BLOCKER | `selectors._hits_for(MATCH_PATH)` reached from the research planners (review PR-602) | THE `path` SELECTOR KIND IS NOT CONFINED TO THE RESEARCH TREE, so routing without a deny lets a research MUTATION target any file in the repository. `resolve(repo,"research","README.md")` matches `kind='path'` and returns the repo's own README. `plan_set_outcome` then plans a frontmatter rewrite of it; `plan_mv`/`plan_set_assign` raise `AttributeError` on `R.parse_name(...).kind`; `run_set_outcome`/`run_set_priority` raise `ValueError` at `target.relative_to(root)`. | Driven at review: `README.md` -> `kind='path'`, 1 path, not under the research root; `plan_set_outcome` planned 26200 bytes (`agent_workflows/cli.py` -> 635622); `parse_name('README.md')` -> `(None, "name must include a '.<kind>' suffix before '.md'")` -> `AttributeError: 'NoneType' object has no attribute 'kind'`. `selectors.resolve_one` and `cli._resolve_selectors_with_kinds` both already `deny=frozenset({MATCH_PATH})`. |
| F-9 | LOW | `tests/test_command_surface_declarations.py` (review PR-605) | The suite does NOT verify `archive`'s declared flag surface. The only shipped assertion is `find_undeclared_leaves(...) == set()` (leaves, not flags); only `prompts new` has a declared-flags-vs-parser test. So E-07's `legacy_flags` edit is unverified by any green run. | `tests/test_command_surface_declarations.py` contains one test, asserting zero undeclared leaves; `rg -n legacy_flags tests/` -> hits only in `test_prompts_new.py`, `test_workflow_artifacts_prune.py`, `test_installer.py`, `conformance_matrix.py`. |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the stated symptoms; E-02 reproduces the two hazards review found.
2. E-03 teaches `record_dirs` the legacy research path (the prerequisite that makes routing non-regressive); E-04 adds the ONE confined research resolver every verb below calls.
3. E-05 factors a path-keyed per-doc planner.
4. E-06 routes targeted archive through the confined helper; E-07 adds `--force`.
5. E-08 routes rename/group; E-09 routes set-outcome/set-priority.
6. E-10 adds the two guard tests; E-11 adds parity and refusal tests; E-12 runs the suite and re-measures.

## Deferred / out of scope (with reason)

- Porting research readers onto `artifact_meta`.
  - Carrier-Declined: owned by spec 4sd62s (routes research readers through artifact_meta); a spec is not an accepted carrier type.
  - Rationale: that spec routes research readers through the metadata store later; landing this first leaves exactly one resolver for it to port instead of five private loops.
- Changing the bare age sweep.
  - Carrier-Declined: it selects by age and citation, not by selector, so the single-resolver claim does not govern it.

## Scope check

- Over-scope: none.
- Under-scope: closed by review. The plan originally declared `agent_workflows/selectors.py` READ-ONLY and asserted the routing was behavior-preserving; both were wrong (F-7, F-8), so `selectors.py` is now IN scope for the ONE additive `record_dirs` change (E-03) and nothing else - the ambiguity POLICY in `resolve_for_mutation` is consumed and never edited. The repo-root threading the original under-scope note speculated about is now a decided instruction in E-08/E-09 (thread from the callers; there is no inverse of `resolve_research_root`).
- Scope-Paths justification: `selectors.py` holds the legacy research read path (E-03, additive, proven non-perturbing by V-03); the three research modules hold the bypasses and the new confined helper; `cli.py` and `command_surface.py` hold the `--force` registration and declaration; `tests/test_research_archive.py` holds the existing archive fixtures (`rg -l run_archive tests` -> `tests/test_research_archive.py`, `tests/test_plans_archive.py`; the latter is the plans backend and is not touched); `tests/test_cli_find.py` holds the per-kind selector semantics contract (`ArtifactsNotReferencesTests`, `PerKindSemanticsTests`), which is where the no-leak-to-another-type case for E-03 belongs.

## Required tests / validation

- The two GUARD cases (E-10): legacy-layout parity and out-of-tree-path confinement, each shown FAILING with its own guard reverted. These are the cases that distinguish this fix from a regression.
- New behavioral cases in `tests/test_research_archive.py` (E-11), with the path-token parity, status refusal, rename refusal and set-outcome refusal shown FAILING before the change and the id6/setid/no-match/apply cases passing before and after.
- `tests/test_research_cmd_create.py` green after E-09 (5 `plan_set_outcome` call sites pass `research_root` positionally).
- `tests/test_command_surface_declarations.py` plus a DIRECT assertion on `get_declaration("archive").legacy_flags` after E-07 (F-9: the suite alone does not cover it).
- Bare `python3 -m pytest` before and after; E-01 re-run in preview.

## Spec / documentation sync

- N/A for specs: this makes the code match the claim already stated in `selectors`'s module docstring and the ruled `resolve_for_mutation` policy; no spec text changes, and no `.spec.md` is in `- Scope-Paths:`.
- The `aw archive` epilog gains nothing beyond the `--force` help line; no README change.

## Open questions

### OQ-01: Should a status selector on `aw archive` act on all matches (like setid) or refuse without `--force`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Refuse without `--force`, from repository evidence: that is the human-ruled policy `resolve_for_mutation` already implements (IPD `laykok` OQ-01) and applies to every other type's mutating verbs; measured F-5/F-6 show it returns exactly that refusal for `reference` and `archive`. Adopting the shared policy is the point of the fix, and it answers backlog `mblu3p`'s warning that routing would make `aw archive research archive` start relocating 32 documents: it will not, without an explicit `--force`.

### OQ-02: Does this change what id6 and setid targets archive today?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No, for conformant documents IN A MIGRATED-LAYOUT REPO: measured F-5 (`awmetastore` 7 = 7; `i5gj61` 1), and re-measured at review that no document in this tree has a filename id6 or setid differing from its declared `id:`/`set:` (0 of 122), so the read-the-declared-field change is a no-op here. The one intended difference is that the resolver reads the DECLARED `id:` rather than the filename slot (backlog `mblu3p` consequence 2), which E-11 case (1) pins as parity with `aw find`. REVISED BY REVIEW: the answer is NOT unconditionally "no". On a LEGACY-layout repo it was "nothing archives at all" (F-7), which is why E-03 is now a prerequisite rather than an assumption.

### OQ-03: Should the legacy research read path be fixed in `selectors.record_dirs`, or worked around inside the research helper?

- Blocking: no
- Status: resolved
- Owner: review (see review record `me227c` D-1)
- Resolution or deferral rationale: FIX IT IN `selectors.record_dirs`, from repository evidence. `record_dirs` is documented as the answer to "directories to search for a record type ... so this works for a bare/unregistered repo too", and it ALREADY carries per-type literal fallbacks for exactly this purpose; research's legacy nesting is simply missing from that list while `record_producers._LEGACY_RECORD_CLASS_SUBPATHS["research"] == "docs/research"` names it. A workaround inside the research helper would leave `aw find research` still blind to the legacy layout, which is the very per-verb divergence this plan exists to remove. Measured non-perturbing on this repo (V-03 requires the before/after proof), and additive by construction because `_add` no-ops a missing directory.

### OQ-04: Should the research helper deny the `path` selector kind, or accept a path that happens to be a research doc?

- Blocking: no
- Status: resolved
- Owner: review (see review record `me227c` D-2)
- Resolution or deferral rationale: DENY the kind AND confine to the research root (belt and braces), from repository evidence and measurement. `selectors.resolve_one` denies `MATCH_PATH` and `cli._resolve_selectors_with_kinds` (behind `aw find`) denies it too, so denying it is the SHIPPED convention for a per-type surface rather than a new restriction, and it keeps the plan's own parity claim honest (`aw find research <path>` matches nothing today either). The confinement is kept beside the deny because the deny is a policy argument a later edit can drop, while the confinement is a property of the research verbs themselves: measured at review, an unconfined path reaches a planned frontmatter rewrite of `README.md` and two distinct unhandled exceptions. Consequence accepted and recorded: E-11's "repo-relative path token" parity case must use a path to a REAL research document and assert it is REFUSED, matching `aw find`, rather than asserting it resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste every E-01 command's output with the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste, for the legacy-layout temp repo, `R.resolve_research_root(root)`, `selectors.record_dirs(root, "research")` and `selectors.resolve_for_mutation(root, "research", "<id6>")` showing the disagreement; and for the real tree, `selectors.resolve(Path('.'), 'research', 'README.md')` showing `kind='path'` with a non-research file, plus `R.parse_name('README.md')` returning None. Both must be REPRODUCED, not asserted from this plan's prose.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `selectors._record_dirs_cached` diff; `selectors.record_dirs(Path('.'), 'research')` BEFORE and AFTER on this repo, proving them IDENTICAL; the E-02(a) fixture's `record_dirs` and `resolve_for_mutation` now returning that document; and `record_dirs` for `plans` and `specs` unchanged (the no-leak check). Note `_record_dirs_cached` is `functools`-cached, so clear the cache or use a fresh process when comparing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new helper's source; then its return value for (a) a real research id6, (b) a setid, (c) a repo-relative path to a real research doc, (d) `README.md`, and (e) `agent_workflows/cli.py`. Cases (c), (d) and (e) MUST ALL be refusals with empty path sets (c by the `MATCH_PATH` deny, d and e by the deny and the confinement both). Also paste the three-module import succeeding.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of `plan_transition`/`plan_transition_for_path`, the `rg -n "plan_transition\("` caller list, and a narrowed run of `tests/test_research_archive.py` passing before any routing change.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the diff of `run_archive`'s targeted branch and, on the E-11 fixture, the preview output for an id6, a setid, `reference` without and with `--force`, and an unknown token (which must still be the exit-0 empty result, NOT a refusal).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `aw archive --help` lines showing `--force`, the `legacy_flags` diff, the `_run_archive` lines showing `vars(args)` is copied, `python3 -c "from agent_workflows import command_surface as cs; print(cs.get_declaration('archive').legacy_flags)"` showing `--force` present, and the narrowed surface tests passing. The direct print is REQUIRED: no shipped test compares `archive`'s declared flags to its parser, so a green suite alone does not prove the declaration was updated.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the diff of `_find_by_id6`/`plan_set_assign`/`plan_mv` (including the threaded `repo_root` and the non-parsing-name guard), `aw rename research <a real id6>` previewing as today, `aw rename research reference` (refusal text), and `plan_mv` with a NON-research path returning an error rather than raising `AttributeError`.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the diff of `plan_set_outcome`/`plan_set_priority` with the chosen `repo_root` threading and the stated reason, a refusal from `plan_set_outcome` for a status token, a refusal for a non-research path token (NOT a planned rewrite of it), and `python3 -m pytest tests/test_research_cmd_create.py -o addopts="" -q` passing with its count.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste both guard tests' source and a run showing them PASS; then, with the E-03 hunk temporarily reverted, the legacy-layout case FAILING, and with the E-04 confinement temporarily reverted, the confinement case FAILING. A guard test that passes with its guard removed proves nothing and must be rewritten.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest tests/test_research_archive.py -o addopts="" -q` passing with its count; then the same with the E-06 to E-09 hunks temporarily reverted, showing the four named cases FAILING and the preserved-behavior cases passing; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste the bare `python3 -m pytest` summary BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and the E-01 previews re-run after the change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: twelve items in five groups, one concern (one selector resolver for the research mutating verbs). E-03 and E-04 are separate from the routing items deliberately: each is a PREREQUISITE GUARD with its own failure mode and its own guard test (E-10), and review measured that routing without either one is a regression rather than a fix. E-06/E-08/E-09 are three verbs with three different call signatures and three different crash sites, so they are not one pass.

WHAT A HUMAN IS APPROVING. `aw archive`, `aw rename`, `aw group`, and `aw research set-outcome`/`set-priority` for research resolve their selector the same way `aw find research` does. id6 and setid targets do what they do today. A selector that matches several documents by status or filename fragment now REFUSES with an explanation and a `--force` hint instead of silently matching nothing; `aw archive` gains that `--force` flag. This is the widening backlog `mblu3p` flagged, delivered under the existing human-ruled policy, so nothing moves in bulk without `--force`. This graduates backlog `mblu3p` and inherits its `- Blocks-Release: next`.

TWO THINGS REVIEW ADDED THAT A HUMAN SHOULD SEE, because both change a shipped behavior beyond the stated concern. FIRST, `selectors.record_dirs` learns the LEGACY research directory `.agents/docs/research` (E-03). That is a one-line additive change to the SHARED resolver every record type and every verb routes through, so although it is proven non-perturbing on this repo (which has no `.agents/`), it necessarily widens what `aw find research`, `aw show` and friends see on a legacy-layout repo - from nothing to the documents that are actually there. Without it, review measured that this plan's routing turns a working `aw archive research <id6>` into a silent no-match on such a repo. SECOND, a path selector is REFUSED by the research mutating verbs (E-04, OQ-04) rather than accepted. That matches `aw find` and `selectors.resolve_one`, which both already deny the kind; it is stated plainly because the plan's original wording promised the opposite ("a path selector to a research doc now works"), and review measured that honoring it would let `aw research set-outcome README.md` plan a rewrite of the repository README.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `selectors.py` (the `_record_dirs_cached` legacy-research path ONLY, never the ambiguity policy), the three research modules, `cli.py` (`p_archive` `--force` only), `command_surface.py` (the `archive` declaration's `legacy_flags` only), `tests/test_research_archive.py`, and `tests/test_cli_find.py` (the E-03 no-leak case only). If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-10 and V-11 must show the new tests FAILING before the change, and V-10 specifically must show each GUARD test failing with its own guard reverted - a guard test that passes without its guard proves nothing. NEVER run `aw archive ... --apply`, `aw rename ... --apply`, `aw group ... --apply`, or `aw research set-outcome/set-priority ... --apply` against the real `.aw/records/research/` tree while executing this plan: every applied test uses a temp repo. This matters more than usual here, because review measured that an unconfined path selector plans a frontmatter rewrite of real non-research files.

STOP CONDITION (a genuinely unsafe state, distinct from the scope fence): if E-03's before/after comparison shows `selectors.record_dirs` CHANGING for this repo or for any non-research type, stop and report rather than proceeding. That would mean the additive change is not additive, and every verb for every record type routes through that function.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `mblu3p` `done` with `--evidence` citing the executed plan; its release gate is preserved by that handoff.
